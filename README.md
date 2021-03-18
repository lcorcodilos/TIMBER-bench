# TIMBER Bench

Tool to run and maintain TIMBER validation and benchmarking tasks. Built to handle the JME modules in comparison to the NanoAOD-tools but infrastructure could be used for other purposes of running and tracking tests.

Uses an SQlite database to track runs locally.

Main scripts to run:
- run.py: Actually run the processing in one of the frameworks (TIMBER or NanoAODtools - assumes both are installed and setup). Can submit a payload which is framework agnostic and specifies things like the input files, year, an identifying tag, etc.
- validation.py: Takes as input the identifying tag and looks for the corresponding TIMBER and NanoAODtools outputs for that tag (using a search of the SQLite database). The validation will randomly select events in the full set (skipping every 1 to 10 events randomly) and then select a random jet from the event to compare across frameworks. The comparison is for each variable is calculated as (TIMBER-NanoAODtools)/NanoAODtools. The JES_comp is known not to match between the two frameworks because of the fundamentally different approach to what is stored in the output branches. For a comparison of the JES, look at either pt_comp or mass_comp.

### Needs and Wants
- [ ] Tools to select runs via SQL and display via a table or graph