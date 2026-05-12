from dynaconf import Dynaconf

settings = Dynaconf(envvar_prefix="SIM6502", settings_files=["sim6502.toml", ".sim6502.toml"], environments=True)

# `envvar_prefix` = export envvars with `export DYNACONF_FOO=bar`.
# `settings_files` = Load these files in the order.
