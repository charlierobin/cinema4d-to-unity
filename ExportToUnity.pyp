import c4d, os, sys

from c4d import plugins, utils, documents, gui, bitmaps, threading

#path = c4d.storage.GeGetC4DPath( c4d.C4D_PATH_PREFS ) + "/symbolcache"
#if os.path.exists( path ): os.remove( path )

folder = os.path.dirname( __file__ )
if folder not in sys.path: sys.path.insert( 0, folder )

# constants

MAIN_COMMAND_PLUGIN_ID = 1034321
MAIN_COMMAND_NAME = "Do the export to Unity"
MAIN_COMMAND_HELP = "A plug in that helps with getting stuff out of Cinema 4D and into Unity"

MAIN_MENU_TITLE = "Unity"
MAIN_PLUGIN_COMMAND = "PLUGIN_CMD_" + str( MAIN_COMMAND_PLUGIN_ID )

MAIN_TAG_PLUGIN_ID = 1034322
MAIN_TAG_TAGNAME = "Export to Unity"
MAIN_TAG_DESCRIPTION = "ExportToUnity"
MAIN_TAG_DESCRIPTION_NO_FBX = "ExportToUnityNoFBX"

STOP_TAG_PLUGIN_ID = 1039243
STOP_TAG_TAGNAME = "Exclude object and children"
STOP_TAG_DESCRIPTION = "StopTag"

TOGGLE_CLEAR_CONSOLE_COMMAND_PLUGIN_ID = 1039238
TOGGLE_CLEAR_CONSOLE_COMMAND = "PLUGIN_CMD_" + str( TOGGLE_CLEAR_CONSOLE_COMMAND_PLUGIN_ID )
TOGGLE_CLEAR_CONSOLE_COMMAND_NAME = "Clear console each time"
TOGGLE_CLEAR_CONSOLE_COMMAND_HELP = "Clears console before starting Unity export"

TOGGLE_DO_SAVE_COMMAND_PLUGIN_ID = 1039239
TOGGLE_DO_SAVE_COMMAND = "PLUGIN_CMD_" + str( TOGGLE_DO_SAVE_COMMAND_PLUGIN_ID )
TOGGLE_DO_SAVE_COMMAND_NAME = "Do Cinema 4D “Save” command"
TOGGLE_DO_SAVE_COMMAND_HELP = "Does a standard Cinema 4D save command before doing the Unity export"

# various options/flags used with c4d.documents.SaveDocument in "Export" method

SAVE_DOCUMENT_FLAGS = c4d.SAVEDOCUMENTFLAGS_DONTADDTORECENTLIST

C4D_OPTION_SAVE_AS_C4D = c4d.FORMAT_C4DEXPORT
C4D_OPTION_SAVE_AS_FBX = 1026370

FBX_EXPORTER_ID = 1026370

# command codes ( for use with c4d.CallCommand )

COMMAND_CURRENT_STATE_TO_OBJECT = 12233
COMMAND_SELECT_CHILDREN = 16388
COMMAND_CONNECT_AND_DELETE = 16768
COMMAND_DELETE = 12109
COMMAND_CLEAR_CONSOLE = 13957
COMMAND_SAVE = 12098
COMMAND_SHOW_CONSOLE = 12305

# preferences ( c4d.plugins.GetWorldPluginData etc )

PREF_DO_C4D_SAVE_COMMAND = 1
PREF_DO_CLEAR_CONSOLE = 2
PREF_LAST_PATH = 3

# file type extensions

FILEEXTENSION_FBX = "fbx"
FILEEXTENSION_C4D = "c4d"

# defaults (for new tags applied to objects for the first time)

TAG_DEFAULT_FILEFORMAT = 10001   #c4d.EXPORTTOUNITY_FILEFORMAT_FBX
#TAG_DEFAULT_FILEFORMAT = c4d.EXPORTTOUNITY_FILEFORMAT_FBX

# miscellaneous

NEWLINE = "\n"
PRINTED_NEWLINE = " " + NEWLINE

MINIMUM_C4D_VERSION_REQUIRED_FOR_FBX_OVERRIDE = 16000
NAME_OF_EDITOR_MENUS = "M_EDITOR"

# constants END

print( "Export To Unity" )

class ExportToUnity( plugins.CommandData ):
    
    def __init__( self ):
        
        self.TempDocumentNameCounter = 0
        self.UsersFBXSettings = {}
        
    def Preflight( self, doc ):
        
        paths = []
        thereWereErrors = False
        
        object = doc.GetFirstObject()
        
        if object == None: return thereWereErrors
    
        while object:
    
            enabledUnityTags = self.GetEnabledUnityTags( object )
            enabledStopTags = self.GetEnabledStopTags( object )
    
            if len( enabledUnityTags ) > 0 and len( enabledStopTags ) > 0: 
                
                print( "There is a stop tag on an object with an export tag (" + object.GetName() + "). The stop tag will be ignored." )
                print( PRINTED_NEWLINE )
    
            for tag in enabledUnityTags: 
    
                tag[ c4d.EXPORTTOUNITY_ERRORS ] = ""
                tag[ c4d.EXPORTTOUNITY_WARNINGS ] = ""
                tag[ c4d.EXPORTTOUNITY_FINAL_PATH ] = ""
                
                if tag[ c4d.EXPORTTOUNITY_PATH ] == "":
                    
                    tag[ c4d.EXPORTTOUNITY_ERRORS ] = tag[ c4d.EXPORTTOUNITY_ERRORS ] + "Please specify an export path." + NEWLINE
                    thereWereErrors = True
    
                else:
    
                    if not os.path.exists( tag[ c4d.EXPORTTOUNITY_PATH ] ):
                        tag[ c4d.EXPORTTOUNITY_ERRORS ] = tag[ c4d.EXPORTTOUNITY_ERRORS ] + "Export path does not exist." + NEWLINE
                        thereWereErrors = True
    
                finalPath = tag[ c4d.EXPORTTOUNITY_PATH ]
                filetype = FILEEXTENSION_C4D
                
                if tag[ c4d.EXPORTTOUNITY_FILEFORMAT ] == c4d.EXPORTTOUNITY_FILEFORMAT_FBX: filetype = FILEEXTENSION_FBX
            
                filename = object.GetName()
                
                if tag[ c4d.EXPORTTOUNITY_FILENAME_OVERRIDE ]: filename = tag [ c4d.EXPORTTOUNITY_FILENAME_OVERRIDE ]

                if "/" in filename:
                    tag[ c4d.EXPORTTOUNITY_WARNINGS ] = tag[ c4d.EXPORTTOUNITY_WARNINGS ] + "Forward slashes not allowed in file names, replaced with “-”." + NEWLINE
                    filename = filename.replace( "/", "-" )

                if ":" in filename:
                    tag[ c4d.EXPORTTOUNITY_WARNINGS ] = tag[ c4d.EXPORTTOUNITY_WARNINGS ] + "Colons not allowed in file names, replaced with “-”." + NEWLINE
                    filename = filename.replace( ":", "-" )

                if "\\" in filename:
                    tag[ c4d.EXPORTTOUNITY_WARNINGS ] = tag[ c4d.EXPORTTOUNITY_WARNINGS ] + "Back slashes not allowed in file names, replaced with “-”." + NEWLINE
                    filename = filename.replace( "\\", "-" )

                finalPath = os.path.join( finalPath, filename + "." + filetype )

                if finalPath in paths:
                    tag[ c4d.EXPORTTOUNITY_ERRORS ] = tag[ c4d.EXPORTTOUNITY_ERRORS ] + "The path " + finalPath + " is already being used by another export. This would result in an overwritten file." + NEWLINE
                    thereWereErrors = True                    
                else:
                    paths.append( finalPath )
                
                tag[ c4d.EXPORTTOUNITY_FINAL_PATH ] = finalPath

            object = self.GetNextObject( object )
            
        return thereWereErrors
     
    def PrintErrors( self, doc ):
        
        c4d.CallCommand( COMMAND_SHOW_CONSOLE )
        
        object = doc.GetFirstObject()
        
        if object == None: return ok
    
        while object:
    
            enabledUnityTags = self.GetEnabledUnityTags( object )
    
            for tag in enabledUnityTags: 
    
                data = tag.GetDataInstance()
                
                if data[ c4d.EXPORTTOUNITY_ERRORS ]:
                    
                    print( object.GetName() + " (tag: " + tag.GetName() + ")" )
                    
                    print( data[ c4d.EXPORTTOUNITY_ERRORS ] )
                
                    print( PRINTED_NEWLINE )
                
            object = self.GetNextObject( object )    
    
    def StoreUsersFBXSettings( self ):
        
        fbxExportSettings = GetFBXExporter()
        
        if fbxExportSettings is not None:
            
            for setting in fbxExportSettings.GetData(): 
                
                key = setting[ 0 ]
                value = setting[ 1 ]
                
                self.UsersFBXSettings[ key ] = value
                            
    def RestoreUsersFBXSettings( self ):
        
        fbxExportSettings = GetFBXExporter()
        
        if fbxExportSettings is not None:
            
            for key, value in self.UsersFBXSettings.items(): fbxExportSettings[ key ] = value
            
    def GetNextObject( self, object ):

        if object == None: return None

        if object.GetDown(): return object.GetDown()

        while not object.GetNext() and object.GetUp(): object = object.GetUp()

        return object.GetNext()
    
    def HasExportToUnityTag( self, object, checkForEnabledTagsOnly = False ):
    
        for tag in object.GetTags():
            
            if tag.GetType() == MAIN_TAG_PLUGIN_ID:
                
                return True
            
                #if checkForEnabledTagsOnly:
                    
                    #if tag[ c4d.EXPRESSION_ENABLE ]: return True
                    
                #else:
                
                    #return True
            
        return False
    
    def HasStopTag( self, object, checkForEnabledTagsOnly = False ):
    
        for tag in object.GetTags():
            
            if tag.GetType() == STOP_TAG_PLUGIN_ID:
                
                return True
            
                #if checkForEnabledTagsOnly:
                    
                    #if tag[ c4d.EXPRESSION_ENABLE ]: return True
                    
                #else:
                
                    #return True
            
        return False
    
    def GetUnityTags( self, object, getEnabledTagsOnly = True ):
        
        tags = []
    
        for tag in object.GetTags():
            
            if tag.GetType() == MAIN_TAG_PLUGIN_ID:
            
                tags.append( tag )
                
                #if getEnabledTagsOnly:
        
                    #if tag[ c4d.EXPRESSION_ENABLE ]: tags.append( tag )        
    
                #else:
                    
                    #tags.append( tag )

        return tags
    
    def GetEnabledUnityTags( self, object ):
        
        return self.GetUnityTags( object, True )
        
    def GetEnabledStopTags( self, object ):
        
        return self.GetStopTags( object, True )
    
    def GetStopTags( self, object, getEnabledTagsOnly = True ):
        
        tags = []
    
        for tag in object.GetTags():
            
            if tag.GetType() == STOP_TAG_PLUGIN_ID:
            
                tags.append( tag )
            
                #if getEnabledTagsOnly:
        
                    #if tag[ c4d.EXPRESSION_ENABLE ]: tags.append( tag )        
    
                #else:
                    
                    #tags.append( tag )

        return tags
    
    def TrimDownwards( self, startObject ):
        
        toDelete = []
        
        nextChild = startObject.GetDown()
    
        while nextChild:
            
            if self.HasExportToUnityTag( nextChild ) or self.HasStopTag( nextChild ):
            
                toDelete.append( nextChild )
            
            else:
                
                toAddToToDelete = self.TrimDownwards( nextChild )
                
                toDelete = toDelete + toAddToToDelete
                
            nextChild = nextChild.GetNext()        
        
        return toDelete
    
    def Trim( self, startObject, doc ):
    
        toDelete = self.TrimDownwards( startObject )
    
        for object in toDelete:
            doc.SetSelection( object, c4d.SELECTION_NEW )
            c4d.CallCommand( COMMAND_DELETE )
             
    def Export( self, doc, object, tag ):
        
        objectName = object.GetName()
        
        print( objectName + " (tag: " + tag.GetName() + ")  ➡  " + tag[ c4d.EXPORTTOUNITY_FINAL_PATH ] )
        
        if tag [ c4d.EXPORTTOUNITY_WARNINGS ]:
            
            print( tag[ c4d.EXPORTTOUNITY_WARNINGS ] )
            print( PRINTED_NEWLINE )
        
        theNewDocument = c4d.documents.IsolateObjects( doc, [ object ] )
        theNewDocument.SetDocumentName( "temp-export-to-unity-" + str( self.TempDocumentNameCounter ) )
        self.TempDocumentNameCounter = self.TempDocumentNameCounter + 1
        c4d.documents.InsertBaseDocument( theNewDocument )
        c4d.documents.SetActiveDocument( theNewDocument )
        
        theNewDocument.SetActiveObject( theNewDocument.GetFirstObject() )
        self.Trim( theNewDocument.GetActiveObject(), theNewDocument )
       
        if tag[ c4d.EXPORTTOUNITY_DO_CURRENT_STATE_TO_OBJECT ]:
            theNewDocument.SetActiveObject( theNewDocument.GetFirstObject() )
            c4d.CallCommand( COMMAND_CURRENT_STATE_TO_OBJECT )      
            c4d.CallCommand( COMMAND_DELETE )
        
        if tag[ c4d.EXPORTTOUNITY_DO_CONNECT_AND_DELETE ]:
            theNewDocument.SetActiveObject( theNewDocument.GetFirstObject() )
            c4d.CallCommand( COMMAND_SELECT_CHILDREN )
            c4d.CallCommand( COMMAND_CONNECT_AND_DELETE )        
        
        theFinalObject = theNewDocument.GetFirstObject()
        theFinalObject.SetName( objectName )
        
        if tag[  c4d.EXPORTTOUNITY_FILEFORMAT ] == c4d.EXPORTTOUNITY_FILEFORMAT_FBX:
        
            saveOptions = C4D_OPTION_SAVE_AS_FBX
            
            self.RestoreUsersFBXSettings()
            
            if tag[ c4d.EXPORTTOUNITY_OVERRIDE_FBX_PREFS ]:
        
                fbxExportSettings = GetFBXExporter()
            
                if fbxExportSettings is not None:
                    
                    fbxExportSettings[ c4d.FBXEXPORT_ASCII ] = tag[ c4d.EXPORTTOUNITY_FBXEXPORT_ASCII_OVERRIDE ]

                    fbxExportSettings[ c4d.FBXEXPORT_LIGHTS ] = tag[ c4d.EXPORTTOUNITY_FBXEXPORT_LIGHTS_OVERRIDE ]
                    fbxExportSettings[ c4d.FBXEXPORT_CAMERAS ] = tag[ c4d.EXPORTTOUNITY_FBXEXPORT_CAMERAS_OVERRIDE ]
                    fbxExportSettings[ c4d.FBXEXPORT_SPLINES ] = tag[ c4d.EXPORTTOUNITY_FBXEXPORT_SPLINES_OVERRIDE ]
                    if hasattr( c4d, 'FBXEXPORT_SDS' ): fbxExportSettings[ c4d.FBXEXPORT_SDS ] = tag[ c4d.EXPORTTOUNITY_FBXEXPORT_SDS_OVERRIDE ]

                    fbxExportSettings[ c4d.FBXEXPORT_TRACKS ] = tag[ c4d.EXPORTTOUNITY_FBXEXPORT_TRACKS_OVERRIDE ]
                    fbxExportSettings[ c4d.FBXEXPORT_BAKE_ALL_FRAMES ] = tag[ c4d.EXPORTTOUNITY_FBXEXPORT_BAKE_ALL_FRAMES_OVERRIDE ]
                    fbxExportSettings[ c4d.FBXEXPORT_PLA_TO_VERTEXCACHE ] = tag[ c4d.EXPORTTOUNITY_FBXEXPORT_PLA_TO_VERTEXCACHE_OVERRIDE ]

                    fbxExportSettings[ c4d.FBXEXPORT_SAVE_NORMALS ] = tag[ c4d.EXPORTTOUNITY_FBXEXPORT_SAVE_NORMALS_OVERRIDE ]
                    fbxExportSettings[ c4d.FBXEXPORT_SAVE_VERTEX_MAPS_AS_COLORS ] = tag[ c4d.EXPORTTOUNITY_FBXEXPORT_SAVE_VERTEX_MAPS_AS_COLORS_OVERRIDE ]
                    if hasattr( c4d, 'FBXEXPORT_SAVE_VERTEX_COLORS' ): fbxExportSettings[ c4d.FBXEXPORT_SAVE_VERTEX_COLORS ] = tag[ c4d.EXPORTTOUNITY_FBXEXPORT_SAVE_VERTEX_COLORS_OVERRIDE ]
                    fbxExportSettings[ c4d.FBXEXPORT_TRIANGULATE ] = tag[ c4d.EXPORTTOUNITY_FBXEXPORT_TRIANGULATE_OVERRIDE ]
                    fbxExportSettings[ c4d.FBXEXPORT_SDS_SUBDIVISION ] = tag[ c4d.EXPORTTOUNITY_FBXEXPORT_SDS_SUBDIVISION_OVERRIDE ]

                    fbxExportSettings[ c4d.FBXEXPORT_TEXTURES ] = tag[ c4d.EXPORTTOUNITY_FBXEXPORT_TEXTURES_OVERRIDE ]
                    fbxExportSettings[ c4d.FBXEXPORT_EMBED_TEXTURES ] = tag[ c4d.EXPORTTOUNITY_FBXEXPORT_EMBED_TEXTURES_OVERRIDE ]
                    if hasattr( c4d, 'FBXEXPORT_SUBSTANCES' ): fbxExportSettings[ c4d.FBXEXPORT_SUBSTANCES ] = tag[ c4d.EXPORTTOUNITY_FBXEXPORT_SUBSTANCES_OVERRIDE ]

        else:
            
            saveOptions = C4D_OPTION_SAVE_AS_C4D
        
        c4d.documents.SaveDocument( theNewDocument, tag[ c4d.EXPORTTOUNITY_FINAL_PATH ], SAVE_DOCUMENT_FLAGS, saveOptions )
        c4d.documents.KillDocument( theNewDocument )
    
    def Execute( self, doc ):

        preferences = GetPreferences()
        
        if preferences.GetBool( PREF_DO_CLEAR_CONSOLE ): c4d.CallCommand( COMMAND_CLEAR_CONSOLE )
        if preferences.GetBool( PREF_DO_C4D_SAVE_COMMAND ): c4d.CallCommand( COMMAND_SAVE )

        thereWereErrors = self.Preflight( doc )

        if thereWereErrors:
            self.PrintErrors( doc )
            print( "There were errors. Nothing was exported." )
            return True
        
        self.StoreUsersFBXSettings()
        
        object = doc.GetFirstObject()
        if object == None: return True

        while object:
            enabledUnityTags = self.GetEnabledUnityTags( object )
            for tag in enabledUnityTags: self.Export( doc, object, tag )                
            object = self.GetNextObject( object )
               
        self.RestoreUsersFBXSettings()
        doc.SetActiveTag( doc.GetActiveTag() )
                
        return True

class ToggleClearConsole( plugins.CommandData ):
    
    def Execute( self, doc ):
        
        preferences = GetPreferences()
        preferences.SetBool( PREF_DO_CLEAR_CONSOLE, not preferences.GetBool( PREF_DO_CLEAR_CONSOLE ) )
        
        return True
    
    def GetState( self, doc ):
        
        preferences = GetPreferences()
        
        if preferences.GetBool( PREF_DO_CLEAR_CONSOLE ):
            return c4d.CMD_ENABLED | c4d.CMD_VALUE
        else:
            return c4d.CMD_ENABLED
        
class ToggleDoSave( plugins.CommandData ):
    
    def Execute( self, doc ):
        
        preferences = GetPreferences()
        preferences.SetBool( PREF_DO_C4D_SAVE_COMMAND, not preferences.GetBool( PREF_DO_C4D_SAVE_COMMAND ) )
        
        return True
    
    def GetState( self, doc ):
        
        preferences = GetPreferences()
        
        if preferences.GetBool( PREF_DO_C4D_SAVE_COMMAND ):
            return c4d.CMD_ENABLED | c4d.CMD_VALUE
        else:
            return c4d.CMD_ENABLED
    
class Tag( plugins.TagData ):
    
    def Init( self, tag ):
        
        preferences = GetPreferences()
        tag[ c4d.EXPORTTOUNITY_PATH ] = preferences.GetString( PREF_LAST_PATH )
        tag[ c4d.EXPORTTOUNITY_FILEFORMAT ] = TAG_DEFAULT_FILEFORMAT

        return True

    def GetDEnabling( self, node, id, t_data, flags, itemdesc ):
                 
        fbxSelected = node[ c4d.EXPORTTOUNITY_FILEFORMAT ] == c4d.EXPORTTOUNITY_FILEFORMAT_FBX
        fbxSelectedAndOverrideEnabled = fbxSelected and node[ c4d.EXPORTTOUNITY_OVERRIDE_FBX_PREFS ] == True
        
        if id[ 0 ].id == c4d.EXPORTTOUNITY_OVERRIDE_FBX_PREFS: return fbxSelected
        
        if id[ 0 ].id == c4d.EXPORTTOUNITY_FBXEXPORT_ASCII_OVERRIDE: return fbxSelectedAndOverrideEnabled
        if id[ 0 ].id == c4d.EXPORTTOUNITY_FBXEXPORT_LIGHTS_OVERRIDE: return fbxSelectedAndOverrideEnabled
        if id[ 0 ].id == c4d.EXPORTTOUNITY_FBXEXPORT_CAMERAS_OVERRIDE: return fbxSelectedAndOverrideEnabled
        if id[ 0 ].id == c4d.EXPORTTOUNITY_FBXEXPORT_SPLINES_OVERRIDE: return fbxSelectedAndOverrideEnabled
        if id[ 0 ].id == c4d.EXPORTTOUNITY_FBXEXPORT_SDS_OVERRIDE: return fbxSelectedAndOverrideEnabled
        if id[ 0 ].id == c4d.EXPORTTOUNITY_FBXEXPORT_TRACKS_OVERRIDE: return fbxSelectedAndOverrideEnabled
        if id[ 0 ].id == c4d.EXPORTTOUNITY_FBXEXPORT_BAKE_ALL_FRAMES_OVERRIDE: return fbxSelectedAndOverrideEnabled
        if id[ 0 ].id == c4d.EXPORTTOUNITY_FBXEXPORT_PLA_TO_VERTEXCACHE_OVERRIDE: return fbxSelectedAndOverrideEnabled
        if id[ 0 ].id == c4d.EXPORTTOUNITY_FBXEXPORT_SAVE_NORMALS_OVERRIDE: return fbxSelectedAndOverrideEnabled
        if id[ 0 ].id == c4d.EXPORTTOUNITY_FBXEXPORT_SAVE_VERTEX_MAPS_AS_COLORS_OVERRIDE: return fbxSelectedAndOverrideEnabled
        if id[ 0 ].id == c4d.EXPORTTOUNITY_FBXEXPORT_SAVE_VERTEX_COLORS_OVERRIDE: return fbxSelectedAndOverrideEnabled
        if id[ 0 ].id == c4d.EXPORTTOUNITY_FBXEXPORT_TRIANGULATE_OVERRIDE: return fbxSelectedAndOverrideEnabled
        if id[ 0 ].id == c4d.EXPORTTOUNITY_FBXEXPORT_SDS_SUBDIVISION_OVERRIDE: return fbxSelectedAndOverrideEnabled
        if id[ 0 ].id == c4d.EXPORTTOUNITY_FBXEXPORT_TEXTURES_OVERRIDE: return fbxSelectedAndOverrideEnabled
        if id[ 0 ].id == c4d.EXPORTTOUNITY_FBXEXPORT_EMBED_TEXTURES_OVERRIDE: return fbxSelectedAndOverrideEnabled
        if id[ 0 ].id == c4d.EXPORTTOUNITY_FBXEXPORT_SUBSTANCES_OVERRIDE: return fbxSelectedAndOverrideEnabled
        
        if id[ 0 ].id == c4d.EXPORTTOUNITY_COPY_FBX_PREFS_BUTTON: return fbxSelectedAndOverrideEnabled
        
        #return self.GetDEnabling( node, id, t_data, flags, itemdesc )
        
        return True
    
    def Message( self, node, type, data ):
        
        if type == c4d.MSG_DESCRIPTION_VALIDATE:
            
            nodeData = node.GetDataInstance()            
            preferences = GetPreferences()
            preferences.SetString( PREF_LAST_PATH, nodeData[ c4d.EXPORTTOUNITY_PATH ] )
        
        if type == c4d.MSG_DESCRIPTION_COMMAND:
            
            if data[ 'id' ][ 0 ].id == c4d.EXPORTTOUNITY_COPY_FBX_PREFS_BUTTON:
                
                fbxExportSettings = GetFBXExporter()
            
                if fbxExportSettings is not None:
                    
                    node[ c4d.EXPORTTOUNITY_FBXEXPORT_ASCII_OVERRIDE ] = fbxExportSettings[ c4d.FBXEXPORT_ASCII ]
                    
                    node[ c4d.EXPORTTOUNITY_FBXEXPORT_LIGHTS_OVERRIDE ] = fbxExportSettings[ c4d.FBXEXPORT_LIGHTS ]
                    node[ c4d.EXPORTTOUNITY_FBXEXPORT_CAMERAS_OVERRIDE ] = fbxExportSettings[ c4d.FBXEXPORT_CAMERAS ]
                    node[ c4d.EXPORTTOUNITY_FBXEXPORT_SPLINES_OVERRIDE ] = fbxExportSettings[ c4d.FBXEXPORT_SPLINES ]
                    if hasattr( c4d, 'FBXEXPORT_SDS' ): node[ c4d.EXPORTTOUNITY_FBXEXPORT_SDS_OVERRIDE ] = fbxExportSettings[ c4d.FBXEXPORT_SDS ]
                    
                    node[ c4d.EXPORTTOUNITY_FBXEXPORT_TRACKS_OVERRIDE ] = fbxExportSettings[ c4d.FBXEXPORT_TRACKS ]
                    node[ c4d.EXPORTTOUNITY_FBXEXPORT_BAKE_ALL_FRAMES_OVERRIDE ] = fbxExportSettings[ c4d.FBXEXPORT_BAKE_ALL_FRAMES ]
                    node[ c4d.EXPORTTOUNITY_FBXEXPORT_PLA_TO_VERTEXCACHE_OVERRIDE ] = fbxExportSettings[ c4d.FBXEXPORT_PLA_TO_VERTEXCACHE ]                  

                    node[ c4d.EXPORTTOUNITY_FBXEXPORT_SAVE_NORMALS_OVERRIDE ] = fbxExportSettings[ c4d.FBXEXPORT_SAVE_NORMALS ]
                    node[ c4d.EXPORTTOUNITY_FBXEXPORT_SAVE_VERTEX_MAPS_AS_COLORS_OVERRIDE ] = fbxExportSettings[ c4d.FBXEXPORT_BAKE_ALL_FRAMES ]
                    if hasattr( c4d, 'FBXEXPORT_SAVE_VERTEX_COLORS' ): node[ c4d.EXPORTTOUNITY_FBXEXPORT_SAVE_VERTEX_COLORS_OVERRIDE ] = fbxExportSettings[ c4d.FBXEXPORT_SAVE_VERTEX_COLORS ]
                    node[ c4d.EXPORTTOUNITY_FBXEXPORT_TRIANGULATE_OVERRIDE ] = fbxExportSettings[ c4d.FBXEXPORT_TRIANGULATE ]
                    node[ c4d.EXPORTTOUNITY_FBXEXPORT_SDS_SUBDIVISION_OVERRIDE ] = fbxExportSettings[ c4d.FBXEXPORT_SDS_SUBDIVISION ]
                    
                    node[ c4d.EXPORTTOUNITY_FBXEXPORT_TEXTURES_OVERRIDE ] = fbxExportSettings[ c4d.FBXEXPORT_TEXTURES ]
                    node[ c4d.EXPORTTOUNITY_FBXEXPORT_EMBED_TEXTURES_OVERRIDE ] = fbxExportSettings[ c4d.FBXEXPORT_EMBED_TEXTURES ]
                    if hasattr( c4d, 'FBXEXPORT_SUBSTANCES' ): node[ c4d.EXPORTTOUNITY_FBXEXPORT_SUBSTANCES_OVERRIDE ] = fbxExportSettings[ c4d.FBXEXPORT_SUBSTANCES ]

                else:
                    
                    print( "Could not get the user’s FBX export settings." )
            
        return True

class StopTag( plugins.TagData ):
    
    def Init( self, data ): return True

def GetPreferences():
    
    preferences = c4d.plugins.GetWorldPluginData( MAIN_COMMAND_PLUGIN_ID )
    
    if preferences == None:

        preferences = c4d.BaseContainer()

        result = c4d.plugins.SetWorldPluginData( MAIN_COMMAND_PLUGIN_ID, preferences )    

    if preferences.GetBool( PREF_DO_C4D_SAVE_COMMAND ) == None: preferences.SetBool( PREF_DO_C4D_SAVE_COMMAND, False )
        
    if preferences.GetBool( PREF_DO_CLEAR_CONSOLE ) == None: preferences.SetBool( PREF_DO_CLEAR_CONSOLE, True )   
    
    if preferences.GetString( PREF_LAST_PATH ) == None: preferences.SetString( PREF_LAST_PATH, "" )

    return preferences

def PluginMessage( id, data ):
    
    if id == c4d.C4DPL_BUILDMENU:
        
        mainMenu = gui.GetMenuResource( NAME_OF_EDITOR_MENUS ) 
        pluginsMenu = gui.SearchPluginMenuResource()

        menu = c4d.BaseContainer()
        menu.InsData( c4d.MENURESOURCE_SUBTITLE, MAIN_MENU_TITLE )  
        menu.InsData( c4d.MENURESOURCE_COMMAND, MAIN_PLUGIN_COMMAND )
        menu.InsData( c4d.MENURESOURCE_SEPERATOR, True )
        
        menu.InsData( c4d.MENURESOURCE_COMMAND, TOGGLE_CLEAR_CONSOLE_COMMAND )
        menu.InsData( c4d.MENURESOURCE_COMMAND, TOGGLE_DO_SAVE_COMMAND )
       
        if pluginsMenu:
            mainMenu.InsDataAfter( c4d.MENURESOURCE_STRING, menu, pluginsMenu )
        else:
            mainMenu.InsData( c4d.MENURESOURCE_STRING, menu )
            
def GetFBXExporter():
    
    fbxExporter = None
    
    plugin = plugins.FindPlugin( FBX_EXPORTER_ID, c4d.PLUGINTYPE_SCENESAVER )

    op = {}
    
    if plugin.Message( c4d.MSG_RETRIEVEPRIVATEDATA, op ) :
        
        if "imexporter" in op: fbxExporter = op[ "imexporter" ]
                
    return fbxExporter
    
if __name__ == "__main__":

    theBitmap = bitmaps.BaseBitmap()
    
    theDirectoryPath, theFileName = os.path.split( __file__ )

    theBitmap.InitWith( os.path.join( theDirectoryPath, "res", "icon.tif" ) )

    if c4d.GetC4DVersion() >= MINIMUM_C4D_VERSION_REQUIRED_FOR_FBX_OVERRIDE:

        plugins.RegisterTagPlugin( id = MAIN_TAG_PLUGIN_ID, 
                                   str = MAIN_TAG_TAGNAME, 
                                   description = MAIN_TAG_DESCRIPTION, 
                                   g = Tag, 
                                   icon = theBitmap, 
                                   info = c4d.TAG_MULTIPLE | c4d.TAG_VISIBLE )

    else:
        
        plugins.RegisterTagPlugin( id = MAIN_TAG_PLUGIN_ID, 
                                       str = MAIN_TAG_TAGNAME, 
                                       description = MAIN_TAG_DESCRIPTION_NO_FBX, 
                                       g = Tag, 
                                       icon = theBitmap, 
                                       info = c4d.TAG_MULTIPLE | c4d.TAG_VISIBLE )        

    plugins.RegisterCommandPlugin( id = MAIN_COMMAND_PLUGIN_ID, 
                                   str = MAIN_COMMAND_NAME, 
                                   info = c4d.PLUGINFLAG_HIDEPLUGINMENU, 
                                   icon = theBitmap, 
                                   help = MAIN_COMMAND_HELP, 
                                   dat = ExportToUnity() )

    theBitmap.InitWith( os.path.join( theDirectoryPath, "res", "icon_stop_tag.tif" ) )
    
    plugins.RegisterTagPlugin( id = STOP_TAG_PLUGIN_ID, 
                               str = STOP_TAG_TAGNAME, 
                               description = STOP_TAG_DESCRIPTION, 
                               g = StopTag, 
                               icon = theBitmap, 
                               info = c4d.TAG_VISIBLE )    
    
    plugins.RegisterCommandPlugin( id = TOGGLE_CLEAR_CONSOLE_COMMAND_PLUGIN_ID, 
                                   str = TOGGLE_CLEAR_CONSOLE_COMMAND_NAME, 
                                   info = c4d.PLUGINFLAG_HIDEPLUGINMENU, 
                                   icon = None, 
                                   help = TOGGLE_CLEAR_CONSOLE_COMMAND_HELP, 
                                   dat = ToggleClearConsole() )
    
    plugins.RegisterCommandPlugin( id = TOGGLE_DO_SAVE_COMMAND_PLUGIN_ID, 
                                   str = TOGGLE_DO_SAVE_COMMAND_NAME, 
                                   info = c4d.PLUGINFLAG_HIDEPLUGINMENU, 
                                   icon = None, 
                                   help = TOGGLE_DO_SAVE_COMMAND_HELP, 
                                   dat = ToggleDoSave() )
