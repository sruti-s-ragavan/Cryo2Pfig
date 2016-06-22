1. SSH to babylon server scratch location:
	ssh username@128.193.38.19
	<enter password when prompted>

	This will take you to student's stak space on servers. 

2. Go to folder where simulation runs off of!
	cd /scratch/SrutiSRagavan_vft/

3. Create virtual terminal with tmux
	Type tmux and hit enter; you'll see a green bar with tmux at the bottom.


4. Start virtualenv
	cd venv/
	bash
	source bin/activate
	[prompt changes to prefix (venv)]

5. cd ../Cryo2Pfig

To bulk-convert logs:
	python convert_logs.py <log_files_folder> <db_folder> <manual_navs_folder>
	Ensure log files are of format A.log, and corresponding manual navs have same name as A.sql
	The DB will be present in the <db_folder> you mentioned above. 
	** ALWAYS COPY THE DB after conversion and just operate on the copy!**

To create variations information (collapse) databases
    - python createEquivalentPatchesByExactText.py --> This creates a database called variantstofunctions.db in Cryo2Pfig folder
    - python createEquivalentPatchesByTextAndEdgeSimilarity.py --> This creates a database called variantstofunctions_1.db in Cryo2Pfig

    NOTE: These two DBs have to be in the Cryo2Pfig folder and are a one-time creation!
    - Make sure these file names are set correctly in the XML config file

To run algorithms:
	Make sure your PFIS/algorithm-config.xml has the right configs
	runScript.sh <path_to_db_folder_copy>

To detach TMUX, Hit Ctrl+B D
To attach to same session, tmux attach. 

Use named sessions for TMUX if needed: https://robots.thoughtbot.com/a-tmux-crash-course


