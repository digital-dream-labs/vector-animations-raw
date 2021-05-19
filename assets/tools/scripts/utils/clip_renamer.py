#!/usr/bin/env python

# WIP!

# run this script from a terminal
# requires path of the directory as a first argument

# renames all .json files in the specified directory to be lower case
# if there are .rar files: renames json files inside

# daria.jerjomina@anki.com
# June 1, 2006: started script
# June 2, 20016: works for non-svn and non-git repos
# June 6, 2016: works for svn and git repos

#todo: add searching for clipnames inside any files
#should rename on 21st

import sys
import os
import tarfile

class ClipRenamer:

    def __init__(self):
        self.directory_path = ""
        # for testing only
        # self.directory_path = "/Users/dariajerjomina/workspace/cozmo-assets/trunk/animations"

        # self.commit = False
        # try:
        #     self.directory_path = sys.argv[1]
        # except IndexError:
        #     print os.path
        #     self.directory_path = ""
        #     print "Need to specify the path where json and tar files live"
        #
        # self.version_controll = self.find_version_controll(self.directory_path)

    #------------------------------------------------------------------------------------------
    # Rename full files (for json files)
    #------------------------------------------------------------------------------------------

    def find_version_controll(self, directory_path):
        """
        check if specified directory is in a git or svn repo (recursive up)
        """
        dirs = directory_path.split('/')

        for dir_count in range(0, len(dirs) - 1):
            new_dirs = dirs[1:len(dirs) - dir_count]
            new_dir_path = ""
            for dir in new_dirs:
                new_dir_path += "/"+dir
            if os.path.isdir(new_dir_path+"/.git"):
                return "git"
            if os.path.isdir(new_dir_path + "/.svn"):
                return "svn"
                print ("svn")
        print "This is neither git nor svn repository"
        return ""

    def rename_file(self, version_controll, file_name):
        """
        renames single file to be lower case depending on a version controll system
        """
        os.chdir(self.directory_path)
        file_no_extension = file_name.split(".")[0]
        flie_extension = file_name.split(".")[-1]

        # workaraound over case sensitivness - renaming to temp file first, then making that upper case
        if version_controll == "svn":
            os.system("svn mv "+file_name+" "+file_no_extension+"_temp."+flie_extension)
            # os.system("svn commit -m \"renaming files with clip_renamer, temp files\"")
            os.system("svn mv "+file_no_extension+"_temp."+flie_extension+" "+file_name.lower())
            if self.commit:
                os.system("svn commit -m \"renamed files with clip_renamer\"")

        elif version_controll == "git":
            return #not renaming git repos at this moment
            #merge with master (in case there are differences)
            os.system("git fetch")
            os.system("git merge origin master")
            os.system("git mv " + file_name + " " + file_no_extension + "_temp." + flie_extension)
            os.system("git mv " + file_no_extension + "_temp." + flie_extension + " " + file_name.lower())
            if self.commit:
                os.system("git commit -m\"renamed files with clip_renamer\"")
                os.system("git push origin master")
        else:
            os.rename(file_name, file_name.lower())

    def rename_files(self, directory_path):
        """
        renames files in the specified directory
        """

        if self.directory_path == "":
            return

        for file_to_rename in os.listdir(directory_path):

            if file_to_rename[-5:] == ".json":
                rename_file("svn", file_name) # TODO replace with self.find_version_controll()
                self.edit_clip_name_in_file(file_to_rename.lower())

            if file_to_rename[-4:] == ".tar":
                # extract components of .tar to rename them
                tar = tarfile.open(directory_path + "/" + file_to_rename)
                tar_kids = tar.getnames()
                tar.extractall()
                # repack .tar with new renamed files
                os.remove(directory_path + "/" + file_to_rename)
                tar = tarfile.open(file_to_rename.lower(), "w")
                for kidFile in tar_kids:
                    if kidFile[-5:] == ".json":
                        os.rename(kidFile, kidFile.lower())
                        self.edit_clip_name_in_file(kidFile.lower())
                        tar.add(kidFile.lower())
                        os.remove(kidFile.lower())

                # if need to rename tar files
                # rename_file(self.version_controll, file_name)

    #------------------------------------------------------------------------------------------
    # Replace clip names inside files
    #------------------------------------------------------------------------------------------


    def edit_clip_name_in_file(self, file_path):
        """
        renames clip names in the json file
        """

        data = open(file_path, "r")
        new_data = ""
        for line in open(file_path):
            if "\"Name\": " in line:
                clip_name = line.split("\"")[3]
                line = line.replace(clip_name, clip_name.lower())
            new_data += line
        data.close()

        file_to_edit = open(file_path, "w")
        file_to_edit.write(new_data)
        file_to_edit.close()

    def replace_string_in_file(self, file_path, rename_from, rename_to):

        data = open(file_path, "r")
        new_data = ""
        for line in open(file_path):
            if rename_from in line:
                line = line.replace(rename_from, rename_to)
            new_data += line
        data.close()

        file_to_edit = open(file_path, "w")
        file_to_edit.write(new_data)
        file_to_edit.close()

    def replace_strings_in_file(self, file_path, from_to):
        """
        @param from_to: dictionary of strings, rename from and rename to
        """
        needs_rewriting = False
        data = open(file_path, "r")
        new_data = ""

        for line in open(file_path):
            for rename_from, rename_to in from_to.iteritems():
                if rename_from in line:
                    needs_rewriting = True
                    line = line.replace(rename_from, rename_to)
            new_data += line
        data.close()

        if needs_rewriting:
            file_to_edit = open(file_path, "w")
            file_to_edit.write(new_data)
            file_to_edit.close()

    def get_clip_names(self):
        """
        go through json files of the folder where animation clips live and get their names
        @return: list of animation clip names
        """

        return


    def rename_hardcoded_clipnames(self):
        # recursively go down the directory structure
        # renaming each
        return

if __name__ == "__main__":
    directory_path = "/Users/dariajerjomina/workspace/cozmo-assets/trunk/animations"

    clip_renamer = ClipRenamer()

    # tested replace_strings_in_file, works
    # clip_renamer.replace_strings_in_file("/Users/dariajerjomina/testExport/test",{"test":"Test","Line":"line"})

    #

    #clip_renamer.find_version_controll(clip_renamer.directory_path)
    clip_renamer.rename_files(directory_path)
    # for testing
    #clip_renamer.rename_file("svn", "Daria_Test.json")
