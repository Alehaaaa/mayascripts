# Update Aleha Tools
import maya.cmds as cmds
import shutil, os, requests, urllib2, zipfile


def get_latest_release():
    repo_url = "https://api.github.com/repos/Alehaaaa/mayascripts/releases"

    response = requests.get(repo_url)

    if response.status_code == requests.codes.ok:
        releases_info = response.json()[0]
        latest_release = releases_info["tag_name"]
        if latest_release:
            release = "https://codeload.github.com/Alehaaaa/mayascripts/legacy.zip/refs/tags/{}".format(
                latest_release
            )
            return release


def formatPath(path):
    path = path.replace("/", os.sep)
    path = path.replace("\\", os.sep)
    return path


def download(downloadUrl, saveFile):

    try:
        response = urllib2.urlopen(downloadUrl, timeout=60)
    except:
        pass

    if response is None:
        cmds.warning("Error trying to install.")
        return

    output = open(saveFile, "wb")

    output.write(response.read())
    output.close()
    return output


def install(tool):

    mayaPath = os.environ["MAYA_APP_DIR"]
    scriptPath = mayaPath + os.sep + cmds.about(version=True) + os.sep + "scripts"
    toolsFolder = scriptPath + os.sep + "aleha_tools" + os.sep
    tmpZipFile = "%s%stmp.zip" % (scriptPath, os.sep)
    FileUrl = get_latest_release()

    old_files = ["%s_pyside2.py" % tool, "%s_pyside2.pyc" % tool]

    for file in old_files:
        if os.path.isfile("%s%s%s" % (scriptPath, os.sep, file)):
            os.remove("%s%s%s" % (scriptPath, os.sep, file))

    if os.path.isfile(tmpZipFile):
        os.remove(tmpZipFile)
    if os.path.isdir(toolsFolder):
        shutil.rmtree(toolsFolder)

    output = download(FileUrl, tmpZipFile)

    zfobj = zipfile.ZipFile(tmpZipFile)
    root = zfobj.namelist()[0]

    zfobj_list = [f for f in zfobj.namelist() if "aleha_tools" in f]
    install_tool_files = [f for f in zfobj_list if (tool in f) or ("__init__" in f)]

    for name in install_tool_files:
        print(name)
        uncompressed = zfobj.read(name)

        filename = formatPath("%s%s%s" % (scriptPath, os.sep, name.replace(root, "")))
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
