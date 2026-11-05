# Public BLE calibration scope

This directory is additive. All files tracked at 4d5a73f, including the previous
static experiment, remain byte-identical. Do not change localization algorithms,
re-run old benchmarks, or fit calibration to held-out location labels.

Current stage: download and audit the 2024 public dataset only. A stored RSSI
column is not necessarily an observed receiver. Keep receiver IDs distinct from
target transmitter IDs. Preserve repetitions and unknown sentinel semantics.
No calibration, localization score, or Huawei compliance claim is authorized by
the data audit itself. Use append-only run directories and record source hashes.
