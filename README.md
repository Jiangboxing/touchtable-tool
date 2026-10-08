# Microgrid Touchtable

Educational microgrid application with a browser interface, Node.js middleware,
and a modified Python DEMKit simulation. Includes seven learning goals,
context-based bonus tasks, grid risk feedback and battery teaching strategies.

## Start here

Read [HANDOVER.md](HANDOVER.md) for the architecture, changed files, parameters,
known limitations and validation checklist. This is a development handover;
fresh-machine installation and all scenarios are not yet verified.

## Configuration before starting

1. Install the Python and Node dependencies described in HANDOVER.md.
2. Copy `demkittt/conf/usrconf.example.py` to `demkittt/conf/usrconf.py`.
3. Update all component/workspace paths in that local configuration and the
   paths in `workspace/touchtable/touchtafel.bat` for your checkout.
4. Configure a compatible local InfluxDB instance if database logging is needed.
   The model currently attempts to clear its configured database at startup.
5. Start DEMKit and Node.js, then open http://localhost:3002.

The repository includes frontend assets, the modified DEMKit components and
the ALPG/weather inputs present in the source snapshot. Dependencies, Git
metadata, generated output, caches and real local credentials are excluded.

## Provenance and license

The original projects are DEMKit / University of Twente, DEMKit-Touchtable,
and webbased-visualizer. Preserve their notices. See
[DEMKit license](demkittt/LICENSE.pdf) and the original component notices;
this handover does not relicense third-party code.

This snapshot flattens the original nested repositories into ordinary folders,
so recipients do not need access to the original private Git remotes.
