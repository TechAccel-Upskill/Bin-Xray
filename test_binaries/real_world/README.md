# Real-World Test Data

This folder contains real-world artifacts downloaded and built from well-known open-source packages for Bin-Xray testing.

## Lua (5.4.6)

Source: https://www.lua.org/

Artifacts:
- Binary: `test_binaries/real_world/lua/lua`
- Map: `test_binaries/real_world/lua/lua.map`
- Library dir: `test_binaries/real_world/lua/`
- Static lib: `test_binaries/real_world/lua/liblua.a`

### Suggested Bin-Xray inputs
- `--binary test_binaries/real_world/lua/lua`
- `--map test_binaries/real_world/lua/lua.map`
- `--libdir test_binaries/real_world/lua/`

For web UI, use the same paths in the form fields.
