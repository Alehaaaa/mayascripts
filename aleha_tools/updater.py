class Updater:
    def formatPath(self, path):
        import os

        path = path.replace("/", os.sep)
        path = path.replace("\\", os.sep)
        return path

    def download(self, downloadUrl, saveFile):
        import maya.cmds as cmds

        try:
            from urllib2 import urlopen
        except:
            from urllib.request import urlopen

        response = urlopen(downloadUrl, timeout=60)

        if response is None:
            cmds.warning("Error trying to install.")
            return

        output = open(saveFile, "wb")

        output.write(response.read())
        output.close()
        return output

    def install(self, tool):
        import maya.cmds as cmds
        import os, shutil, zipfile

        mayaPath = os.environ["MAYA_APP_DIR"]
        scriptPath = mayaPath + os.sep + cmds.about(version=True) + os.sep + "scripts"
        toolsFolder = scriptPath + os.sep + "aleha_tools" + os.sep
        tmpZipFile = "%s%stmp.zip" % (scriptPath, os.sep)
        FileUrl = "https://github.com/Alehaaaa/mayascripts/archive/main.zip"

        old_files = ["%s_pyside2.py" % tool, "%s_pyside2.pyc" % tool]

        for file in old_files:
            if os.path.isfile("%s%s%s" % (scriptPath, os.sep, file)):
                os.remove("%s%s%s" % (scriptPath, os.sep, file))

        if os.path.isfile(tmpZipFile):
            os.remove(tmpZipFile)

        # Remove old tool files
        if os.path.isdir(toolsFolder):
            for filename in os.listdir(toolsFolder):
                f = os.path.join(toolsFolder, filename)
                if (tool in f) or ("updater" in f):
                    if os.path.isfile(f):
                        os.remove(f)
                    elif os.path.isdir(f):
                        shutil.rmtree(f)

        output = self.download(FileUrl, tmpZipFile)

        zfobj = zipfile.ZipFile(tmpZipFile)
        root = zfobj.namelist()[0]

        zfobj_list = [f for f in zfobj.namelist() if "aleha_tools" in f]
        updater_script = [f for f in zfobj.namelist() if "updater" in f]
        install_tool_files = [f for f in zfobj_list if (tool in f) or ("__init__" in f)]
        files = install_tool_files + updater_script

        for name in files:
            uncompressed = zfobj.read(name)

            filename = self.formatPath(
                "%s%s%s" % (scriptPath, os.sep, name.replace(root, ""))
            )
            d = os.path.dirname(filename)

            if not os.path.exists(d):
                os.makedirs(d)
            if filename.endswith(os.sep):
                continue

            output = open(filename, "wb")
            output.write(uncompressed)
            output.close()

        zfobj.close()
        if os.path.isfile(tmpZipFile):
            os.remove(tmpZipFile)

        self.add_shelf_button(tool)

    def add_shelf_button(self, tool):
        import maya.cmds as cmds
        import maya.mel as mel
        import os

        currentShelf = cmds.tabLayout(mel.eval("$nul=$gShelfTopLevel"), q=1, st=1)

        def find():
            buttons = cmds.shelfLayout(currentShelf, q=True, ca=True)
            if buttons is None:
                return False
            else:
                for b in buttons:
                    if (
                        cmds.shelfButton(b, exists=True)
                        and cmds.shelfButton(b, q=True, l=True) == tool
                    ):
                        return True
            return False

        if not find():
            cmds.shelfButton(
                parent=currentShelf,
                i=os.path.join(
                    os.environ["MAYA_APP_DIR"],
                    cmds.about(version=True),
                    "scripts",
                    "aleha_tools",
                    "icons",
                    "{}.svg".format(tool),
                ),
                label=tool,
                c="import aleha_tools.{} as {};{}.UI.show_dialog()".format(
                    tool, tool, tool
                ),
                annotation="{} by Aleha".format(tool.title()),
            )
            cmds.confirmDialog(
                title="Added Shelf Button",
                message="Added a Button for {} to the current shelf.".format(
                    tool.title()
                ),
                button=["Ok"],
                defaultButton="Ok",
            )
