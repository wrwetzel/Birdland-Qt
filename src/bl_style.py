# ---------------------------------------------------------------------------
#   Reminder:
#       object.setObjectName("Name")       Still relevant for styling with #object_name.
#       self.findChild(QLabel, "myLabel")  Generally obsolete for all but diagnostics.

#   WRW 3-Mar-2025 - add no-color experiment. Objective is to preserve dimensional
#       style properties while omitting color so user can use external style for color

#   WRW 3-Mar-2025 Recognized need for two selector types by experimentation. Chat confirmed.
#       With this fix all working fine now.

#       QLineEdit#objectName { ... } applies styles only to a QLineEdit with     
#       'objectName', no matter where it is in the hierarchy.  Works well
#       when styling widgets individually.  For Targeting Child Widgets of a Named
#       Parent

#       #objectName QPushButton { ... } applies styles to all QPushButtons inside
#       widget 'objectName'.  Useful for styling multiple buttons within
#       a specific container.

#   WRW 25-Apr-2025 - Try out jinja2 template facility for another approach to
#       appearance (themes, colors, etc.). Looks good, keeping it.

#   padding all;
#   padding top/bottom left/rigt;
#   padding top sides bottom;
#   padding top right bottom left;

# ---------------------------------------------------------------------------

import re
from jinja2 import Template
from Store import Store
from PySide6.QtGui import QColor, QGuiApplication

# ---------------------------------------------------------------------------

StyleSheet = """

QWidget {
     font-size: {{font_size_9}};
     color: {{qwidget_text}};
     background-color: {{qwidget_bg}};
}

#mainTitle {
    font-family: Helvetica;
    font-family: Arial;
    font-size: {{font_size_20}};
    font-weight: bold;
    color: {{title_color}};
}

#subTitle {
    font-family: Times;
    font-size: {{font_size_18}};
    color: {{title_color}};
    font-style: italic;
}

#subSubTitle {
    font-family: Helvetica;
    font-size: {{font_size_10}};
    color: {{title_color}};
    font-style: italic;   
}

/* font-family: Courier;           /* Has ligatures */
/* font-family: Courier New;       /* Darker than Courier */
/* font-family: DejaVu Sans Mono;  /* Not enough leading and no leading option */

#resultsText {
    font-size: {{font_size_9}};
    font-family: 'Noto Sans Mono', 'Courier New', monospace;                                                       
}

#engraveMenu {
     font-size: {{font_size_9}};
}

/* -------------------------------------------------------------- */
/*  WRW 3-Mar-2025 - moved from MyGroupBox */

QGroupBox {
    font: {{font_size_8}};
    border-radius: 0px;             /* 5px */
    margin-top: 8px;                /* Moves title into border, positive moves it up, 10px with checkbox */
    padding-top: 3px;               /* Just a little extra room below the title */
    border: 1px solid {{group_box}};
}

QGroupBox::title {
    subcontrol-origin: margin;
    left: 6px;                      /* Shift title from corner, WRW 8-Apr-2025 was 5 */
    padding: 0px 5px;               /* Add a little horizontal space to title */
    border-radius: 0px;             /* 3px Visible if set background color */
}


/* ------------------------------------------------------------ */
/*  WRW 27-Apr-2025 - Tuning scroll bar - have to do all when
    parameters change color.
*/

QScrollBar:vertical {
    border: none;
    background: transparent;
    width: 8px;
    margin: 0px;
    border: none;
}
QScrollBar::handle:vertical {
    background: {{scroll_bar}};
    min-height: 20px;
    border-radius: 4px;         /* Half of width for perfect capsule */
}
QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0px;
    background: none;
    border: none;
}
QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {
    background: none;
}

/* -------------------------------------------------------------- */

QTableView::verticalHeader { 
    width: 0px;
}

#search-panel QPushButton {
    height: 10px;
    font-size: {{font_size_9}};
    padding: 8px 20px;
    background-color: {{button_bg}};
    color: {{button}};
}

#setlist-tab QPushButton, #canon2file-tab QPushButton {
    height: 10px;
    font-size: {{font_size_9}};
    padding: 8px 20px;
    background-color: {{button_bg}};
    color: {{button}};
}

#setlist-tab QPushButton:disabled {
    height: 10px;
    font-size: {{font_size_9}};
    padding: 8px 20px;
    background-color: {{button_disabled_bg}};
    color: {{button_disabled}};
}

/*  WRW 3-Mar-2025 - moved from bl_main_window.py */
/*  OK had to explicitly name the widget type - QPushButton - in the style as below */
/*   WRW 10-Apr-2025 - don't want color on viewer control buttons, some icon colors makes no sense with it */

#pdfViewerControls QPushButton {
    min-height: 15px;
    max-height: 15px;
    max-width: 15px;
    min-width: 15px;
    font-size: {{font_size_8}};
    padding: 3px 4px;
    border-radius: 4px;
}

/* Explicitly border styling for QComboBox needed - border disappeared when made it editable. */

QComboBox {
    border: 1px solid #808080;
    border-radius: 4px;
    padding: 0px 4px 0px 4px;
    color: {{combo}};
    background-color: {{combo_bg}};
}

#searchButton {
    background-color: #006000;
}

QTableView {
    font-size: {{font_size_8}};
    padding: 0px 0px;              /* OK - padding around outside of table */
    color: {{table}};
}

QHeaderView::section {
    font-weight: bold;
    font-size: {{font_size_9}};
    height: 20px;
    color: {{table}};
    background: {{table_bg_head}};
    border-radius: 6px;
    margin-right: 2px;
    margin-left: 0px;
}

QHeaderView::section:focus,
QHeaderView::section:pressed,
QHeaderView::section:checked,
QHeaderView::section:active {
    background: {{table_bg_head}};
}

QTreeView::header QHeaderView::section {
    background: {{table_bg_head}};
}

QTreeView::item:selected {
    background-color: {{table_bg_sel}};
}

QTreeView::header QHeaderView::section:focus,
QTreeView::header QHeaderView::section:pressed,
QTreeView::header QHeaderView::section:checked,
QTreeView::header QHeaderView::section:active {
    background: {{table_bg_head}};
}

QTableView::item {
    background-color: {{table_bg}}; /* OK */ /* Had to use this to prevent bogus background after sorting tables */
    color: {{table}};
}

QTableView::item:alternate {
    background-color: {{table_bg_alt}};
    color: {{table}};
}

QTableView::item:selected {
    background-color: {{table_bg_sel}};
}

/* ------------------------------------------------------------ */
/* WRW 25-Apr-2025 - Got this tuned nicely */

QTabBar {
    alignment: left;            /* WRW 3-May-2025 - testing on MacOS, tabs were centered */
    /* qproperty-drawBase: 0; */
}

QTabBar::tab {
    font-size: {{font_size_9}};
    border: 1px solid gray;
    background-color: {{tab_bg}};
}

QTabBar::tab:top {
    padding: 3px 10px;  /* Padding inside the tabs */
    margin-left: 0px;
    margin-right: 4px;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
}

QTabBar::tab:left {
    padding: 10px 3px;  /* Padding inside the tabs */
    margin-top: 0px;
    margin-bottom: 4px;
    margin-left: 5px;
    border-right: none;
    border-top-left-radius: 4px;
    border-bottom-left-radius: 4px;
}

QTabBar::tab::selected {
    font-weight: bold;
    background-color: {{tab_bg_selected}};
}

QTabBar::tab::selected:top {
    border-top: 3px solid #8080ff;
}

QTabBar::tab::selected:left {
    border-left: 3px solid #8080ff;
}

/* WRW 8-Apr-2025 some styling withing metadata panel. */
/* WRW 12-Apr-2025 - All borders disappeared on Windows, need some. Leave them in for now. 
        /// RESUME try putting one or more back in.
*/

#leftTabBar::pane, #rightTabBar::pane {
    border: none;   
}

#topTabBar QTabWidget::pane {   /* Applies to all QTabWidget INSIDE topTabBar but not topTabBar */
    /* border: none; */
}

/* ---------------------------------------- */
/* Save in case I need to style pane. */

XQTabWidget::pane {
    padding: 0px;  /* Padding around the content */
    /* background-color: #00ff00; /* OK */
}

/* ------------------------------------------------------------ */

QToolTip {
    padding: 0px 5px 0px 5px;
    border: 2px solid {{tab_bg_selected}};
    color: {{qwidget_text}};
    background-color: {{qwidget_bg}};
    border-radius: 6px;
}

/* ------------------------------------------------------------ */

QLineEdit {
    height: 12px;
    max-width: 100px;
    border-radius: 0px;
    font-size: {{font_size_9}};
    padding: 2px 5px;
    color: {{lineedit}};
    background-color: {{lineedit_bg}};
    border: 1px solid gray;
    border-style: inset;
}

QLineEdit#titleLineEdit {
    color: {{lineedit_title}};
    background-color: {{lineedit_title_bg}};
}

#configureDialog QLineEdit{
    height: 12px;
    max-width: 1000px;          /* Need to override the more general max-width above*/
    border-radius: 0px;
    font-size: {{font_size_9}};
    padding: 2px 5px;
    color: {{lineedit}};
    background-color: {{lineedit_bg}};
    border: 1px solid gray;
    border-style: inset;
}

QTextEdit {
    padding: 0px;
    margin:  0px;
    color: {{textedit}};
    background-color: {{textedit_bg}};
}

#configureDialog QTextEdit {
    color: {{textedit}};
    background-color: {{textedit_bg}};
    padding: 2px 5px;
}

#metadataPanel QTextEdit {   /* All QTextEdit boxes under widget labeled metadataPanel */
    border: none;   
}

/* ------------------------------------------------------------ */

QLabel#configureLabel  {
    font-size: {{font_size_10}};
    font-weight: bold;
    font-style: italic;
}

/* ------------------------------------------------------------ */
/*  WRW 30-Apr-2025 - this is not working, styles likely getting in way.
    Keep for possibility other styles may not interfere.
*/

QSlider::sub-page:horizontal {
    background-color: {{scroll_bar}};   /* filled section left of handle */
}

/* ------------------------------------------------------------ */
/*  WRW 5-May-2025 - Checkboxes not visible on dark theme.
    Lost checkmark and dot after styled, achieve with color, 
    alternative is to add an icon.
*/

QCheckBox, QRadioButton {
    color: {{qwidget_text}};
}

XQCheckBox::indicator, QRadioButton::indicator {
    border: 1px solid {{qwidget_text}};
}

QCheckBox::indicator, QRadioButton::indicator {
    background-color: {{qwidget_bg}};
    border: 1px solid {{qwidget_text}};
}

QCheckBox::indicator:checked, QRadioButton::indicator:checked  {
    background-color: {{scroll_bar}};
    border: 1px solid {{qwidget_text}};
}

QCheckBox::indicator:unchecked:hover, QRadioButton::indicator:unchecked:hover   {
    background-color: {{qwidget_text_dis}};
}

/* ------------------------------------------------------------ */

#canon2file-title {
    font-size: {{font_size_10}};
    font-weight: bold;
}

#aboutVersion {
    font-family: Helvetica;
    font-family: Arial;
    font-size: {{font_size_16}};
    color: {{title_color}};
}

#aboutCopyright{
    font-family: Helvetica;
    font-family: Arial;
    font-size: {{font_size_10}};
    color: {{title_color}};
}

#aboutLicense{
    font-family: Helvetica;
    font-family: Arial;
    font-size: {{font_size_10}};
    color: {{title_color}};
}

#aboutTitle {
    font-family: Helvetica;
    font-family: Arial;
    font-size: {{font_size_20}};
    font-weight: bold;
    color: {{title_color}};
}

#aboutText {
    font-family: Helvetica;
    font-family: Arial;
    font-size: {{font_size_10}};
    color: {{qwidget_text}};
}

/* ------------------------------------------------------------ */

#XconfigureDialog {              /* /// RESUME WRW 27-Apr-2025 - what is this for? */
    font-family: Helvetica;
    font-family: Arial;
    font-size: {{font_size_20}};
    color: #ffffff;
}

/* ------------------------------------------------------------ */

"""

# ---------------------------------------------------------------------------
#   WRW 25-Apr-2025 - Migrating to jinja templates. Idea here is to use stylesheets
#   instead of palettes for getting a handful of color themes.
#   This way we have complete control of the color of each feature of each widget
#   and not dependent on palettes and interactions between palettes and styles.
#   Much cleaner, much easier, wasted a lot of time exploring palettes and stylesheets.

# ------------------------------------------------------------------------------
#   Use this when a simple adjustment will generate a useful related color.

def adjust( color, factor ):
    r, g, b = color
    r = min(255, int(r * factor))
    g = min(255, int(g * factor))
    b = min(255, int(b * factor))
    return (r, g, b)

def adjustHex( color, factor ):
    r = int( color[1:3], 16 )
    g = int( color[3:5], 16 )
    b = int( color[5:7], 16 )
    r = min(255, int(r * factor))
    g = min(255, int(g * factor))
    b = min(255, int(b * factor))
    t = f"#{r:02x}{g:02x}{b:02x}"
    return t

def adjustV( color, factor ):
    h, s, v = color
    v = min(255, int(v * factor))
    return (h, s, v)

# ------------------------------------------------------------------------------
#   It is tempting to put the following in a function but we may need/want to adjust     
#       the parameters of each of the bases differently so keep separate.
#   Define several palettes, one for each appearance.

#   _B0 - Base color
#   _B1 - A little contrast, for tabs, row of table
#   _B2 - A little more contrast, for alternate row of table
#   _T -  Text and icons
#   _Td -  Text and icons disabled
#   _St - Selected tab             
#   _Sr - Selected row in table or tree
#   _A -  Title text box and some buttons, accent or attention
#   _Ad - Button disabled background, text is Td
#   _Xs - Scroll bar
#   _Xt - Table head        
#   _Xg - Group box outline

# Hue: 0-359 (red is at 0°, green at 120°, blue at 240°, etc.)

# ------------------------------------------------------------------------------------------
#   Move into function to avoid globals polution. Called infrequently so inefficiency of
#   multiple executions is irrevalent.

def getThemeData():
    s = Store()
    
    # ---------------------------------------------
    #   Exploring HSV vs RGB - Looks good after some tuning.
    
    if s.Const.Platform == 'MacOS':         # MacOS was a bit darker.
        D = (0, 0, 32*1.5 )
    else:
        D = (0, 0, 32 )

    D_B0 = QColor.fromHsv( *D ).name()
    D_B1 = QColor.fromHsv( *adjustV( D, 1.5 )).name()
    D_B2 = QColor.fromHsv( *adjustV( D, 2 )).name()
    D_T = '#ffffff'
    D_Td = adjustHex( D_T, .5 )
    D_Xg = '#808080'
    D_St = '#800000'
    # D_Sr = QColor.fromHsv( *adjustV( D, 3 )).name()
    D_Sr = '#a00000'
    D_A = '#008000'
    D_Ad= '#408040'
    D_Xs = QColor.fromHsv( 240, 128, 192 ).name()
    D_Xt = QColor.fromHsv( 240, 64, 128 ).name()
    
    # ---------------------------------------------
    
    if s.Const.Platform == 'MacOS':         # MacOS was a bit darker.
        DA = (20, 1.*255, .094*255 * 2 )
    else:
        DA = (20, 1.*255, .094*255 )

    DA_B0 = QColor.fromHsv( *adjustV( DA, 1 )).name()
    DA_B1 = QColor.fromHsv( *adjustV( DA, 2 )).name()
    DA_B2 = QColor.fromHsv( *adjustV( DA, 4 )).name()
    DA_T = '#ffc530'
    DA_Td = adjustHex( DA_T, .5 )
    DA_Xg = '#804000'
    DA_St = '#804000'
    # DA_Sr = QColor.fromHsv( *adjustV( DA, 6 )).name()
    DA_Sr = '#0000a0'
    DA_A =  '#008000'
    DA_Ad = '#408040'
    DA_Xs = QColor.fromHsv( *adjustV( DA, 10 )).name()
    DA_Xt = QColor.fromHsv( *adjustV( DA, 4 )).name()
    
    #   HSV, converter yielded degrees, percent, percent. Change to per-unit and normalize to 255.
    # DB = (26, 40, 54 )      # Started with this in RGB

    if s.Const.Platform == 'MacOS':         # MacOS was a bit darker.
        DB = (210, .52*255, .15*255 )
    else:
        DB = (210, .52*255, .18*255 )

    DB_B0 = QColor.fromHsv( *DB ).name()
    DB_B1 = QColor.fromHsv( *adjustV( DB, 1.5 )).name()
    DB_B2 = QColor.fromHsv( *adjustV( DB, 2 )).name()
    DB_T = '#f0f0ff'
    DB_Td = adjustHex( DB_T, .5 )
    DB_Xg = '#8080c0'
    DB_St = '#800000'
    # DB_Sr = QColor.fromHsv( *adjustV( DB, 2.5 )).name()
    DB_Sr = '#a00000'
    DB_A = '#008000'
    DB_Ad = '#408040'
    DB_Xs = QColor.fromHsv( 240, 128, 192 ).name()
    DB_Xt = QColor.fromHsv( *adjustV( DB, 3 )).name()
    
    DR = (40, 10, 5 )
    DR_B0 = QColor( *adjust( DR, 1 )).name()
    DR_B1 = QColor( *adjust( DR, 2 )).name()
    DR_B2 = QColor( *adjust( DR, 3 )).name()
    DR_T = '#f0f0ff'
    DR_Td = adjustHex( DR_T, .5 )
    DR_Xg = '#c08080'
    DR_St = '#800000'
    # DR_Sr = QColor( *adjust( DR, 4 )).name()
    DR_Sr = '#0000a0'
    DR_A = '#008000'
    DR_Ad = '#408040'
    DR_Xs = QColor.fromHsv( 240, 128, 192 ).name()
    DR_Xt = QColor.fromHsv( 240, 64, 128 ).name()
    DR_Xs = QColor( *adjust( DR, 6 )).name()
    DR_Xt = QColor( *adjust( DR, 4 )).name()

    L = (250, 250, 250 )
    L_B0 = QColor( *adjust( L, 1 )).name()
    L_B1 = QColor( *adjust( L, .98 )).name()
    L_B2 = QColor( *adjust( L, .9 )).name()
    L_T = '#000000'
    L_Td = '#a0a0a0'
    L_Xg = '#c0c0c0'
    L_St = '#ffa0a0'
    # L_Sr = QColor( *adjust( L, .8 )).name()
    L_Sr = '#ffa0a0'
    L_A =  '#a0ffa0'
    L_Ad = '#80c080'
    L_Xs = QColor.fromHsv( 240, 128, 255 ).name()
    L_Xt = QColor.fromHsv( 240, 64, 255 ).name()
    
    LB = (230, 230, 255 )
    LB_B0 = QColor( *adjust( LB, 1 )).name()
    LB_B1 = QColor( *adjust( LB, .98 )).name()
    LB_B2 = QColor( *adjust( LB, .90 )).name()
    LB_T = '#000040'
    LB_Td = '#a0a0ff'
    LB_Xg = '#c0c0c0'
    LB_St = '#ffa0a0'
    # LB_Sr = QColor( *adjust( LB, .8 )).name()
    LB_Sr = '#ffa0a0'
    LB_A = '#a0ffa0'
    LB_Ad = '#80c080'
    LB_Xs = QColor.fromHsv( 240, 128, 255 ).name()
    LB_Xt = QColor.fromHsv( 240, 64, 255 ).name()
    
    #   See: https://colordesigner.io/convert/hextohsv

    #   This is based on PySimpleGUI Kayak
    # 'Kayak': {'BACKGROUND': '#a7ad7f','TEXT': '#000000','INPUT': '#e6d3a8','SCROLL': '#e6d3a8',
    #    'TEXT_INPUT': '#000000','BUTTON': ('#FFFFFF', '#5d907d'),'PROGRESS': DEFAULT_PROGRESS_BAR_COMPUTE,
    #    'BORDER': 1,'SLIDER_DEPTH': 0,'PROGRESS_DEPTH': 0,},

    LBr_B0 = QColor.fromHsv(67.83, 67, 173 ).name()
    LBr_B1 = QColor.fromHsv(67.83, 67, 200 ).name()
    LBr_B2 = QColor.fromHsv(67.83, 67, 225 ).name()      # Alt row in table
    LBr_T = '#000000'
    LBr_Td = '#408070'
    LBr_Xg = '#c0c0c0'
    LBr_St = '#5d907d'                                   # Selected tab
    LBr_St = QColor.fromHsv(157.65, 90, 144 ).name()                                   # Selected tab
    # LBr_Sr = QColor.fromHsv(67.83, 67, 250 ).name()      # Selected row in table
    LBr_Sr = '#5d907d'  
    LBr_A = QColor.fromHsv(157.65, 90, 144 * 1.1 ).name()                                     # Title text and some buttons
    LBr_Ad = '#80c080'
    LBr_Xs = QColor.fromHsv( 67.83, 90, 220 ).name()
    LBr_Xt = QColor.fromHsv( 67.83, 64, 250 ).name()

    # ------------------------------------------------------------------------------------------
    #   Experimental almost fully algorithmic palette generator.
    #   This works remarkably well with only a little hand tweaking.

    Hue = 260
    Dh  = 30
    Val = 32
    Dv = +64
    Sat = 255

    Ex_B0 = QColor.fromHsv(   Hue,               Sat, Val         ).name()
    Ex_B1 = QColor.fromHsv(   Hue,               Sat, Val + Dv    ).name()
    Ex_B2 = QColor.fromHsv(   Hue,               Sat, Val + Dv*2  ).name()
    Ex_T =  QColor.fromHsv(   Hue,               0,   255         ).name()
    Ex_Td =  QColor.fromHsv(   Hue,               0,   255/2      ).name()
    Ex_Xg = '#808080'
    Ex_St = QColor.fromHsv( ( Hue + Dh*1 )%360,  Sat, Val + Dv*2  ).name()
    # Ex_Sr = QColor.fromHsv( ( Hue + Dh*2 )%360,  Sat, Val + Dv*1  ).name()
    Ex_Sr = '#a00000'
    Ex_A =  QColor.fromHsv( ( Hue - Dh*1 )%360,  Sat, Val         ).name()
    Ex_Ad =  QColor.fromHsv( ( Hue - Dh*1 )%360,  Sat/2, Val      ).name()

    Ex_Xs = QColor.fromHsv( 240, 128, 192 ).name()
    Ex_Xt = QColor.fromHsv( 240, 128, 255 ).name()

    Ex_Xs = QColor.fromHsv( ( Hue + Dh*.5 )%360, Sat/2, 192 ).name()
    Ex_Xt = QColor.fromHsv( ( Hue - Dh*.5 )%360, Sat/2, 192 ).name()

    # ------------------------------------------------------------------------------------------
    
    themes = {
        'Name':                 [ 'Exp',     'Light',    'Dark',     'Dark-Blue',  'Dark-Red',  'Dark-Amber', 'Light-Blue',  'PSG-Kayak', ],
        'title_color' :         [ Ex_T,       L_T,        D_T,        DB_T,         DR_T,         DA_T,         LB_T,          LBr_T,     ],
        'qwidget_text' :        [ Ex_T,       L_T,        D_T,        DB_T,         DR_T,         DA_T,         LB_T,          LBr_T,     ],
        'qwidget_text_dis' :    [ Ex_Td,      L_Td,       D_Td,       DB_Td,        DR_Td,        DA_Td,        LB_Td,         LBr_Td,     ],
        'qwidget_bg' :          [ Ex_B0,      L_B0,       D_B0,       DB_B0,        DR_B0,        DA_B0,        LB_B0,         LBr_B0,     ],

        'button' :              [ Ex_T,       L_T,        D_T,        DB_T,         DR_T,         DA_T,         LB_T,          LBr_T,     ],
        'button_bg' :           [ Ex_A,       L_A,        D_A,        DB_A,         DR_A,         DA_A,         LB_A,          LBr_A,     ],

        'button_disabled' :     [ Ex_T,      L_T,        D_T,      DB_T,        DB_T,        DA_T,        LB_T,         LBr_T,     ],
        'button_disabled_bg' :  [ Ex_Ad,      L_Ad,        D_Ad,      DB_Ad,        DR_Ad,        DA_Ad,        LB_Ad,         LBr_Ad      ],

        'tab_bg' :              [ Ex_B1,       L_B1,        D_B1,        DB_B1,         DR_B1,          DA_B1,        LB_B1,          LBr_B1,     ],
        'tab_bg_selected' :     [ Ex_St,       L_St,        D_St,        DB_St,         DR_St,          DA_St,        LB_St,          LBr_St,     ],

        'lineedit' :            [ Ex_T,       L_T,        D_T,        DB_T,         DR_T,          DA_T,        LB_T,          LBr_T,     ],
        'lineedit_bg' :         [ Ex_B1,      L_B1,        D_B1,        DB_B1,         DR_B1,          DA_B1,        LB_B1,          LBr_B1,     ],
        'lineedit_title' :      [ Ex_T,       L_T,        D_T,        DB_T,         DR_T,          DA_T,        LB_T,          LBr_T,     ],
        'lineedit_title_bg' :   [ Ex_A,       L_A,        D_A,        DB_A,         DR_A,          DA_A,        LB_A,          LBr_A,     ],

        'textedit' :            [ Ex_T,       L_T,        D_T,        DB_T,         DR_T,          DA_T,        LB_T,          LBr_T,     ],
        'textedit_bg' :         [ Ex_B1,       L_B1,        D_B1,        DB_B1,         DR_B1,          DA_B1,        LB_B1,          LBr_B1,     ],

        'combo' :               [ Ex_T,       L_T,        D_T,        DB_T,         DR_T,          DA_T,        LB_T,          LBr_T,     ],
        'combo_bg' :            [ Ex_B1,       L_B1,        D_B1,        DB_B1,         DR_B1,          DA_B1,        LB_B1,          LBr_B1,     ],

        'table' :               [ Ex_T,       L_T,        D_T,        DB_T,         DR_T,          DA_T,        LB_T,          LBr_T,     ],
        'table_bg' :            [ Ex_B1,       L_B1,        D_B1,        DB_B1,         DR_B1,          DA_B1,        LB_B1,          LBr_B1,     ],
        'table_bg_alt' :        [ Ex_B2,       L_B2,        D_B2,        DB_B2,         DR_B2,          DA_B2,        LB_B2,          LBr_B2      ],
        'table_bg_sel' :        [ Ex_Sr,       L_Sr,        D_Sr,        DB_Sr,         DR_Sr,          DA_Sr,        LB_Sr,          LBr_Sr,     ],
        'table_bg_head' :       [ Ex_Xt,      L_Xt,       D_Xt,       DB_Xt,        DR_Xt,         DA_Xt,       LB_Xt,         LBr_Xt,    ],

        'scroll_bar' :          [ Ex_Xs,      L_Xs,       D_Xs,       DB_Xs,        DR_Xs,         DA_Xs,       LB_Xs,         LBr_Xs,    ],
        'group_box' :           [ Ex_Xg,       L_Xg,        D_Xg,        DB_Xg,         DR_Xg,          DA_Xg,        LB_Xg,          LBr_Xg,     ],

    }
    
    return themes

# ---------------------------------------------------------------------------
#   So don't have to keep table above and menu in sync.

def getThemeNames():
    themes = getThemeData()
    return themes[ 'Name' ]

# ---------------------------------------------------------------------------

def pt2px(points: float) -> int:
    screen = QGuiApplication.primaryScreen()
    # dpi = screen.logicalDotsPerInch()  # You can also use physicalDotsPerInch()
    dpi = screen.physicalDotsPerInch()  # You can also use physicalDotsPerInch()
    px = f"{int(points * dpi / 72)}px"
    return px

# ---------------------------------------------------------------------------
#   Return style sheet rendered to colors specified by 'name' colume in themes table.

def getStyle( name=None ):
    s = Store()
    style_template = Template( StyleSheet )

    try:
        idx = getThemeData()['Name'].index( name )

    except ValueError:
        s.msgWarn( f"ERROR-DEV: name '{name}' not recognized at getStyle()" )
        idx = getThemeData()['Name'].index( 'Dark' )

    colors = { key: values[idx] for key, values in getThemeData().items() if key != 'Name' }

    if s.Const.Platform == 'MacOS':
        font_sizes = {
            'font_size_8' : pt2px( 8 ),
            'font_size_9' : pt2px( 9 ),
            'font_size_10' : pt2px( 10 ),
            'font_size_12' : pt2px( 12 ),
            'font_size_16' : pt2px( 16 ),
            'font_size_18' : pt2px( 18 ),
            'font_size_20' : pt2px( 20 ),
        }
    else:
        font_sizes = {
            'font_size_8'  : '8pt',
            'font_size_9'  : '9pt',
            'font_size_10' : '10pt',
            'font_size_12' : '12pt',
            'font_size_16' : '16pt',
            'font_size_18' : '19pt',
            'font_size_20' : '20pt',
        }

    qss = style_template.render( **{ **colors, **font_sizes} )
    return qss

# ---------------------------------------------------------------------------
#   Return one element from themes table selected by theme name and item name.
#   Note, not a rendered stylesheet.

def getOneStyle( name, item ):

    s = Store()
    style_template = Template( StyleSheet )

    try:
        idx = getThemeData()['Name'].index( name )

    except ValueError:
        s.msgWarn( f"ERROR-DEV: name '{name}' not recognized at getOneStyle()" )
        idx = getThemeData()['Name'].index( 'Dark' )

    return getThemeData()[ item ][ idx ]

# ---------------------------------------------------------------------------
#   Removes color-related properties from a given stylesheet. Used with
#   qdarkstyle

def getStyleGeometry( tone=None ):

    color_properties = [
        "color", "background", "background-color", "border-color",
        "selection-color", "selection-background-color", "alternate-background-color",
        "border-top", "border-left",
    ]

    pattern = r"\b(" + "|".join(color_properties) + r")\s*:\s*[^;]+;"   # Create a regex pattern to remove only color-related styles

    t = re.sub(pattern, "", StyleSheet, flags=re.IGNORECASE)        # Remove matching properties

    style_template = Template( t )
    qss = style_template.render( )
    return qss

# ---------------------------------------------------------------------------
