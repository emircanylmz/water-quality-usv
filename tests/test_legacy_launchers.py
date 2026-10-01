def test_legacy_launchers_resolve_to_platform_implementations():
    import DualControl
    import keyboard
    import telemetry
    import xslx_logger
    import xslx_to_kml
    from pc import keyboard as pc_keyboard
    from pc import telemetry as pc_telemetry
    from pc import xlsx_logger, xlsx_to_kml
    from raspberry import dual_control

    assert DualControl.main is dual_control.main
    assert keyboard.main is pc_keyboard.main
    assert telemetry.main is pc_telemetry.main
    assert xslx_logger.main is xlsx_logger.main
    assert xslx_to_kml.main is xlsx_to_kml.main
