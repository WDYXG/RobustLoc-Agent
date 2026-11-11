package org.robustloc.field;

import android.Manifest;
import android.app.Activity;
import android.bluetooth.BluetoothAdapter;
import android.bluetooth.BluetoothManager;
import android.bluetooth.le.AdvertiseCallback;
import android.bluetooth.le.AdvertiseData;
import android.bluetooth.le.AdvertiseSettings;
import android.bluetooth.le.BluetoothLeAdvertiser;
import android.bluetooth.le.BluetoothLeScanner;
import android.bluetooth.le.ScanCallback;
import android.bluetooth.le.ScanFilter;
import android.bluetooth.le.ScanResult;
import android.bluetooth.le.ScanSettings;
import android.content.ClipData;
import android.content.ClipboardManager;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.PackageManager;
import android.location.Location;
import android.location.LocationListener;
import android.location.LocationManager;
import android.os.Build;
import android.os.Bundle;
import android.os.Handler;
import android.os.Looper;
import android.os.ParcelUuid;
import android.os.SystemClock;
import android.view.View;
import android.view.WindowManager;
import android.widget.Button;
import android.widget.EditText;
import android.widget.LinearLayout;
import android.widget.ScrollView;
import android.widget.TextView;

import org.json.JSONArray;
import org.json.JSONException;
import org.json.JSONObject;

import java.io.File;
import java.io.FileOutputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.util.ArrayList;
import java.util.Arrays;
import java.util.Collections;
import java.util.UUID;

public final class MainActivity extends Activity {
    private static final int EXPORT = 20;
    private static final int PERMISSIONS = 21;
    private final Handler handler = new Handler(Looper.getMainLooper());
    private EditText reporterInput;
    private EditText ticketInput;
    private TextView status;
    private String installationId;
    private JSONObject ticket;
    private JSONObject report;
    private byte[] exportBytes;
    private BluetoothLeScanner scanner;
    private BluetoothLeAdvertiser advertiser;
    private LocationManager locations;
    private long clockUtc;
    private long clockElapsed;
    private long start;
    private long end;
    private boolean scanRequested;
    private boolean advertising;
    private final Runnable beginScan = this::startScan;
    private final Runnable endScan = () -> finishCapture("complete", "");

    @Override
    protected void onCreate(Bundle state) {
        super.onCreate(state);
        SharedPreferences preferences = getPreferences(MODE_PRIVATE);
        installationId = preferences.getString("installation", "");
        if (installationId.isEmpty()) {
            installationId = UUID.randomUUID().toString();
            preferences.edit().putString("installation", installationId).apply();
        }
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
        LinearLayout content = new LinearLayout(this);
        content.setOrientation(LinearLayout.VERTICAL);
        int margin = (int) (20 * getResources().getDisplayMetrics().density);
        content.setPadding(margin, margin, margin, margin);
        TextView heading = new TextView(this);
        heading.setTextSize(23);
        heading.setText("RobustLoc 静态 BLE 采集");
        content.addView(heading);
        reporterInput = new EditText(this);
        reporterInput.setHint("手机编号，例如 P01");
        reporterInput.setSingleLine(true);
        reporterInput.setText(preferences.getString("reporter", ""));
        content.addView(reporterInput);
        ticketInput = new EditText(this);
        ticketInput.setHint("粘贴本次试验的 JSON 采集票");
        ticketInput.setMinLines(3);
        ticketInput.setText(preferences.getString("ticket", ""));
        content.addView(ticketInput);
        button(content, "复制手机登记信息", v -> copyRegistration());
        button(content, "准备采集", v -> arm());
        button(content, "启动目标广播", v -> startBeacon());
        button(content, "结束当前操作", v -> {
            finishCapture("interrupted", "operator_stop");
            stopBeacon();
        });
        button(content, "导出当前活动的手机记录", v -> exportCampaign());
        status = new TextView(this);
        status.setText("先登记手机编号。采集时保持本页在前台。");
        status.setTextIsSelectable(true);
        content.addView(status);
        ScrollView scroll = new ScrollView(this);
        scroll.setOnApplyWindowInsetsListener((view, insets) -> {
            view.setPadding(insets.getSystemWindowInsetLeft(), insets.getSystemWindowInsetTop(),
                            insets.getSystemWindowInsetRight(), insets.getSystemWindowInsetBottom());
            return insets;
        });
        scroll.addView(content);
        setContentView(scroll);
    }

    private void button(LinearLayout parent, String label, View.OnClickListener click) {
        Button button = new Button(this);
        button.setText(label);
        button.setOnClickListener(click);
        parent.addView(button);
    }

    private void show(String message) { status.setText(message); }

    private static void put(JSONObject object, String name, Object value) {
        try {
            object.put(name, value);
        } catch (JSONException error) {
            throw new IllegalArgumentException(error);
        }
    }

    private static String identifier(String value) {
        if (!value.matches("[A-Za-z0-9_-]{1,48}")) {
            throw new IllegalArgumentException("编号须为 1–48 位字母、数字、下划线或短横线。");
        }
        return value;
    }

    private JSONObject registration() {
        JSONObject result = new JSONObject();
        String reporter = identifier(reporterInput.getText().toString().trim());
        put(result, "reporter_id", reporter);
        put(result, "installation_id", installationId);
        put(result, "manufacturer", Build.MANUFACTURER);
        put(result, "model", Build.MODEL);
        put(result, "os_release", Build.VERSION.RELEASE);
        put(result, "sdk_int", Build.VERSION.SDK_INT);
        getPreferences(MODE_PRIVATE).edit().putString("reporter", reporter).apply();
        return result;
    }

    private void copyRegistration() {
        try {
            String data = registration().toString();
            getSystemService(ClipboardManager.class).setPrimaryClip(ClipData.newPlainText("手机登记", data));
            show("已复制手机登记 JSON。\n" + data);
        } catch (IllegalArgumentException error) {
            show(error.getMessage());
        }
    }

    private JSONObject readTicket() throws JSONException {
        String text = ticketInput.getText().toString().trim();
        JSONObject value = new JSONObject(text);
        if (!"robustloc-ticket-v1".equals(value.getString("schema"))) {
            throw new IllegalArgumentException("采集票版本不匹配。");
        }
        identifier(value.getString("campaign_id"));
        identifier(value.getString("trial_id"));
        UUID.fromString(value.getString("target_uuid"));
        long duration = value.getLong("duration_ms");
        if (duration < 5000 || duration > 120000 || value.getLong("start_utc_ms") <= 0) {
            throw new IllegalArgumentException("采集窗须为 5–120 秒。");
        }
        getPreferences(MODE_PRIVATE).edit().putString("ticket", text).apply();
        return value;
    }

    private boolean permit(boolean beacon) {
        ArrayList<String> required = new ArrayList<>();
        if (!beacon) {
            required.add(Manifest.permission.ACCESS_COARSE_LOCATION);
            required.add(Manifest.permission.ACCESS_FINE_LOCATION);
        }
        if (Build.VERSION.SDK_INT >= 31) {
            required.add(Manifest.permission.BLUETOOTH_CONNECT);
            required.add(beacon ? Manifest.permission.BLUETOOTH_ADVERTISE : Manifest.permission.BLUETOOTH_SCAN);
        }
        if (required.stream().allMatch(p -> checkSelfPermission(p) == PackageManager.PERMISSION_GRANTED)) {
            return true;
        }
        requestPermissions(required.toArray(new String[0]), PERMISSIONS);
        show("请授予附近设备及本次操作所需的定位权限，然后重新点击。");
        return false;
    }

    private BluetoothAdapter bluetooth() {
        BluetoothAdapter adapter = getSystemService(BluetoothManager.class).getAdapter();
        if (adapter == null || !adapter.isEnabled()) {
            throw new IllegalStateException("请先打开蓝牙。");
        }
        return adapter;
    }

    private void arm() {
        if (report != null || advertising) {
            show("请先结束当前操作。");
            return;
        }
        try {
            JSONObject selected = readTicket();
            JSONObject device = registration();
            long requestedStart = selected.getLong("start_utc_ms");
            if (requestedStart - System.currentTimeMillis() < 4000) {
                throw new IllegalArgumentException("采集窗即将开始或已过期，请使用新试验票。");
            }
            if (captureFile(selected).exists()) {
                throw new IllegalArgumentException("本试验已有记录。补采请使用新试验票。");
            }
            if (!permit(false)) return;
            scanner = bluetooth().getBluetoothLeScanner();
            if (scanner == null) throw new IllegalStateException("本手机的 BLE 扫描器不可用。");
            ticket = selected;
            clockElapsed = SystemClock.elapsedRealtimeNanos();
            clockUtc = System.currentTimeMillis();
            start = requestedStart;
            end = start + ticket.getLong("duration_ms");
            report = new JSONObject();
            put(report, "schema", "robustloc-capture-v1");
            put(report, "ticket", ticket);
            put(report, "device", device);
            put(report, "armed_utc_ms", now());
            put(report, "scan_started_utc_ms", JSONObject.NULL);
            put(report, "packets", new JSONArray());
            put(report, "fixes", new JSONArray());
            locations = getSystemService(LocationManager.class);
            for (String provider : Arrays.asList(LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER)) {
                if (locations.isProviderEnabled(provider)) {
                    locations.requestLocationUpdates(provider, 1000L, 0f, locationListener, Looper.getMainLooper());
                }
            }
            handler.postDelayed(beginScan, Math.max(0, start - 2000 - now()));
            show("已准备。定位预热中，保持本页前台。\n试验 " + ticket.getString("trial_id"));
        } catch (JSONException | RuntimeException error) {
            if (report != null) finishCapture("error", error.toString());
            else show(error.getMessage());
        }
    }

    private long utc(long elapsedNanos) { return clockUtc + (elapsedNanos - clockElapsed) / 1000000L; }
    private long now() { return utc(SystemClock.elapsedRealtimeNanos()); }

    private void startScan() {
        if (report == null) return;
        try {
            ScanFilter filter = new ScanFilter.Builder().setServiceUuid(
                ParcelUuid.fromString(ticket.getString("target_uuid"))).build();
            ScanSettings settings = new ScanSettings.Builder()
                .setScanMode(ScanSettings.SCAN_MODE_LOW_LATENCY).setReportDelay(0).build();
            put(report, "scan_started_utc_ms", now());
            scanRequested = true;
            scanner.startScan(Collections.singletonList(filter), settings, scanCallback);
            handler.postDelayed(endScan, Math.max(0, end - now() + 250));
            show("BLE 采集中。目标包 0 条。");
        } catch (JSONException | RuntimeException error) {
            finishCapture("error", error.toString());
        }
    }

    private final LocationListener locationListener = new LocationListener() {
        @Override public void onLocationChanged(Location location) {
            if (report == null || !location.hasAccuracy()) return;
            JSONObject fix = new JSONObject();
            put(fix, "t_utc_ms", utc(location.getElapsedRealtimeNanos()));
            put(fix, "lat", location.getLatitude());
            put(fix, "lon", location.getLongitude());
            put(fix, "accuracy_m", (double) location.getAccuracy());
            put(fix, "provider", location.getProvider());
            put(fix, "mock", Build.VERSION.SDK_INT >= 31 ? location.isMock() : location.isFromMockProvider());
            report.optJSONArray("fixes").put(fix);
        }
        @Override public void onStatusChanged(String provider, int state, Bundle extras) {}
        @Override public void onProviderEnabled(String provider) {}
        @Override public void onProviderDisabled(String provider) {}
    };

    private final ScanCallback scanCallback = new ScanCallback() {
        @Override public void onScanResult(int type, ScanResult result) {
            handler.post(() -> {
                if (report == null || result.getScanRecord() == null ||
                    result.getScanRecord().getServiceUuids() == null ||
                    !result.getScanRecord().getServiceUuids().contains(
                        ParcelUuid.fromString(ticket.optString("target_uuid")))) return;
                long time = utc(result.getTimestampNanos());
                if (time < start || time >= end) return;
                JSONObject packet = new JSONObject();
                put(packet, "t_utc_ms", time);
                put(packet, "rssi_dbm", result.getRssi());
                JSONArray packets = report.optJSONArray("packets");
                packets.put(packet);
                show("BLE 采集中。目标包 " + packets.length() + " 条。");
            });
        }
        @Override public void onScanFailed(int code) {
            handler.post(() -> finishCapture("error", "scan_failed_" + code));
        }
    };

    private File captureFile(JSONObject selected) {
        return new File(new File(getFilesDir(), selected.optString("campaign_id")),
                        selected.optString("trial_id") + ".json");
    }

    private void finishCapture(String outcome, String reason) {
        if (report == null) return;
        handler.removeCallbacks(beginScan);
        handler.removeCallbacks(endScan);
        if (scanRequested) {
            try { scanner.stopScan(scanCallback); } catch (RuntimeException ignored) {}
        }
        scanRequested = false;
        if (locations != null) {
            try { locations.removeUpdates(locationListener); } catch (RuntimeException ignored) {}
        }
        put(report, "ended_utc_ms", now());
        put(report, "clock_drift_ms", System.currentTimeMillis() - now());
        put(report, "status", outcome);
        put(report, "reason", reason);
        File destination = captureFile(ticket);
        destination.getParentFile().mkdirs();
        File temporary = new File(destination.getParentFile(), destination.getName() + ".tmp");
        try (FileOutputStream stream = new FileOutputStream(temporary)) {
            stream.write(report.toString().getBytes(StandardCharsets.UTF_8));
            stream.getFD().sync();
            if (destination.exists() || !temporary.renameTo(destination)) {
                throw new IllegalStateException("无法保存采集记录。");
            }
            show("已保存 " + outcome + "，目标包 " + report.optJSONArray("packets").length() +
                 " 条。可导出 JSON。");
        } catch (Exception error) {
            show("保存失败：" + error.getMessage());
        } finally {
            report = null;
        }
    }

    private void startBeacon() {
        if (report != null || advertising) {
            show("请先结束当前操作。");
            return;
        }
        try {
            JSONObject selected = readTicket();
            if (!permit(true)) return;
            advertiser = bluetooth().getBluetoothLeAdvertiser();
            if (advertiser == null) throw new IllegalStateException("本手机不支持 BLE 广播。");
            AdvertiseData payload = new AdvertiseData.Builder()
                .addServiceUuid(ParcelUuid.fromString(selected.getString("target_uuid"))).build();
            AdvertiseSettings settings = new AdvertiseSettings.Builder()
                .setAdvertiseMode(AdvertiseSettings.ADVERTISE_MODE_LOW_LATENCY)
                .setTxPowerLevel(AdvertiseSettings.ADVERTISE_TX_POWER_MEDIUM)
                .setConnectable(false).build();
            advertising = true;
            advertiser.startAdvertising(settings, payload, beaconCallback);
            show("等待系统启动目标广播。");
        } catch (JSONException | RuntimeException error) {
            advertising = false;
            show(error.getMessage());
        }
    }

    private final AdvertiseCallback beaconCallback = new AdvertiseCallback() {
        @Override public void onStartSuccess(AdvertiseSettings settings) {
            show("目标正在广播。保持本页前台，并放在测绘目标点。");
        }
        @Override public void onStartFailure(int code) {
            advertising = false;
            show("目标广播启动失败：" + code);
        }
    };

    private void stopBeacon() {
        if (advertising && advertiser != null) {
            try { advertiser.stopAdvertising(beaconCallback); } catch (RuntimeException ignored) {}
            show("目标广播已停止。");
        }
        advertising = false;
    }

    private void exportCampaign() {
        if (report != null || advertising) {
            show("请先结束当前操作。");
            return;
        }
        try {
            String campaign = readTicket().getString("campaign_id");
            JSONArray records = new JSONArray();
            File[] files = new File(getFilesDir(), campaign).listFiles((dir, name) -> name.endsWith(".json"));
            if (files != null) {
                Arrays.sort(files);
                for (File file : files) {
                    records.put(new JSONObject(new String(Files.readAllBytes(file.toPath()), StandardCharsets.UTF_8)));
                }
            }
            if (records.length() == 0) {
                show("当前活动还没有保存的采集记录。");
                return;
            }
            JSONObject bundle = new JSONObject();
            put(bundle, "schema", "robustloc-capture-bundle-v1");
            put(bundle, "reports", records);
            exportBytes = bundle.toString(2).getBytes(StandardCharsets.UTF_8);
            Intent intent = new Intent(Intent.ACTION_CREATE_DOCUMENT).addCategory(Intent.CATEGORY_OPENABLE)
                .setType("application/json")
                .putExtra(Intent.EXTRA_TITLE, campaign + "-" + installationId + ".json");
            startActivityForResult(intent, EXPORT);
        } catch (Exception error) {
            show("导出失败：" + error.getMessage());
        }
    }

    @Override protected void onActivityResult(int request, int result, Intent data) {
        super.onActivityResult(request, result, data);
        if (request != EXPORT) return;
        if (result == RESULT_OK && data != null && exportBytes != null) {
            try (OutputStream stream = getContentResolver().openOutputStream(data.getData(), "wt")) {
                if (stream == null) throw new IllegalStateException("无法打开导出文件。");
                stream.write(exportBytes);
                show("导出完成。请通过现场组约定的方式交给数据管理员。");
            } catch (Exception error) {
                show("导出失败：" + error.getMessage());
            }
        }
        exportBytes = null;
    }

    @Override protected void onPause() {
        finishCapture("interrupted", "left_foreground");
        stopBeacon();
        super.onPause();
    }
}
