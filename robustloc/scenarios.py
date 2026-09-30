"""Protected scenario definitions. All lengths are in metres."""
SCENARIOS = {
    'clean': dict(n=16, position_sigma=0.1, rssi_sigma=0.3, hetero=False, outliers=0., geometry='ring'),
    'gaussian': dict(n=16, position_sigma=1., rssi_sigma=2., hetero=False, outliers=0., geometry='ring'),
    'heteroscedastic': dict(n=16, position_sigma=1.5, rssi_sigma=2., hetero=True, outliers=0., geometry='ring'),
    'outliers10': dict(n=16, position_sigma=1.5, rssi_sigma=2., hetero=True, outliers=.1, geometry='ring'),
    'outliers20': dict(n=16, position_sigma=1.5, rssi_sigma=2., hetero=True, outliers=.2, geometry='ring'),
    'outliers30': dict(n=16, position_sigma=1.5, rssi_sigma=2., hetero=True, outliers=.3, geometry='ring'),
    'poor_geometry': dict(n=16, position_sigma=1.5, rssi_sigma=2., hetero=True, outliers=.2, geometry='arc'),
    'sparse': dict(n=4, position_sigma=1.5, rssi_sigma=2., hetero=True, outliers=.2, geometry='ring'),
}
