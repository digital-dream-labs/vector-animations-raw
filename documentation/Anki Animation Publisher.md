# Anki Animation Publisher

Created by Chris Rogers  Sep 11, 2018

BETA

To launch the beta version cut-n-paste this into a python script editor or shelf editor.  Eventually the existing export button will trigger the publisher.

```
    import ankimaya.publish as  publish
    reload(publish)
    publish.main()
```

This script combines exporting and committing to version control.

The top of the UI lists the clips in the scene file that you can also see in the Game Exporter.

The button marked “Publish” will run through the steps listed at the bottom of the page.  For now, you can select which steps to run, when its completely rolled out some steps will not be optional.  The steps are:

* Make sure file named
* Make sure file is saved
* Check to see if SVN is available
* Check that file is locked before exporting
* Make sure there is a comment for this
* Do Export
* Do SVN Commit
* Do Unlock file at end

Just as with the "export" button, this will export the JSON files and the TAR file and save the Maya scene file.  The maya and tar file will be submitted to SVN.

The three tabs at the top will show the main UI, a list of output files with their SVN revision and a log of everything that happened.

