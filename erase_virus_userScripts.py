# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!
 
# PLEASE READ!
 
# put this script in this directory (OR add it to your userSetup.py file. this code MUST be in userSetup.py to work):
# "%USERPROFILE%\Documents\maya\####\scripts"
# or
# "~/maya/####/scripts"
 
# this script creates a maya "callback" that executes every time ANY file is created/loaded/referenced in maya.
# The "callback" kills all <SCRIPT NODES>, making sure the scene is SAFE for users
# >>> Autodesk Maya Scanner tool does NOT clean <SCRIPT NODES> in references <<<
 
# !!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

import maya.cmds as cmds
import maya.OpenMaya

if cmds.about(v=True) <= '2020':
    
    def killAllScriptNodes(clientData):
    
        attributeSettings = {
            "scriptType": 0, # enum is "Demand" (dont want script to run randomly even if its empty)
            "before": "", # clear before script
            "after": "", # clear after script
            "sourceType": 0, # MEL
            "ignoreReferenceEdits": 0} #Record reference edits (so the scipt works with references)
    
        scriptNodes = cmds.ls(typ="script") #check for any scriptnodes are in scene
        scriptNodes = [s for s in scriptNodes if '_gene' in s]
        scriptNodesBefore = scriptNodes
        cmds.delete(scriptNodes) #delete them! theyre not safe for work
        scriptNodes = cmds.ls(typ="script") #check again
        scriptNodesAfter = scriptNodes
        scriptNodesDeleted = len(scriptNodesBefore) - len(scriptNodesAfter)
        if scriptNodesDeleted:
            print(str(scriptNodesDeleted) + " Script Nodes deleted")
    
        for sNode in scriptNodes:
            for attr, val in attributeSettings.items():
                attrType = cmds.attributeQuery(attr, node=sNode, attributeType=1)
                if attrType == "typed":
                    cmds.setAttr(sNode + "." + attr, val, typ="string")
                else:
                    cmds.setAttr(sNode + "." + attr, val)
    
        scriptNodesEmptied = len(cmds.ls(typ="script"))
        if scriptNodesEmptied:
            print(str(scriptNodesEmptied) + " Script Nodes emptied")
        else:
            cmds.warning("Could not fix script nodes!")
    
    maya.OpenMaya.MSceneMessage.addCallback(maya.OpenMaya.MSceneMessage.kAfterSceneReadAndRecordEdits, killAllScriptNodes)
