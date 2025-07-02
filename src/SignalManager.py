#!/usr/bin/env python
# ----------------------------------------------------------------------------
#   SignalManager.py

#   WRW 11-Feb-2025 - Manage signal/slot connections between modules.
#       Modified from suggestions from ChatGPT.

#   With this the binding between signal and slot is done with text names.

#   CONSIDER - add metaclass logic here and for all singletons elsewhere?
#       Not yet, not a strong reason for that.

#   WRW 19-Apr-2025 - Yesterday added record and playback of managed signal emit()s.
#   This is an experiment to assess feasibility of regression tests using just
#   managed signals and their associated values. It works but it is insufficient
#   as too much happening by mouse action without signals and with native signals.
#   Might be OK for limited testing but will take a LOT more work for full recording
#   and playback: register all classes, capture mouse and record clicks on UI elements,
#   more. Since the purpose is just development regression testing it is not worth it
#   as the user will have no need for record & playback. Leave as is for now, no
#   plans to expand it.

# ----------------------------------------------------------------------------

#   Usage:
#   Signal and slot registration can be done in module class __init__() or
#       in bl_main.c RegisterNonClassSignals() class when the module is not using classes.

#   Register each signal and slot only once.
#   Connect one->one, one->many, many->one as needed.

#   In signaling module:
#   Signals must be registered in the namespace of the signal definition.
#       from SignalManager import SigMan
#       Initialize:
#           self.sigman = SigMan()
#       Define signal
#           sig_s1 = Signal( str )
#       Register signal:
#           self.sigman.register_signal( "signal_name", self.sig_s1 )

#   In slot module:
#   Slots must be registered in the namespace of the slot definition.
#       from SignalManager import SigMan
#       Initialize:
#           self.sigman = SigMan()
#       Register slot
#           self.sigman.register_slot( 'slot_r1', self.receive_message_fcn )
#           self.sigman.register_slot( 'slot_r1', receive_message_fcn )

#   Connect signals and slots in higher-level code:
#       from SignalManager import SigMan
#       Initialize:
#           self.sigman = SigMan()
#       Connect the signals and slots
#           sigman.connect( 'sig_s1', 'slot_r1' )

#       Emit signal from internal signal catcher connected outside of SignalManager:
#           self.sigman.emit( "sig_cell_clicked", text )       ( received as: *argv, **kwargs )

#       Or directly in the connect statement with lambda:
#           self.toc.sig_cell_clicked.connect( lambda x, y, z: self.sigman.emit( "sig_toc_cell_clicked", x, y, z ))

# ----------------------------------------------------------------------------

import os
import sys
import inspect
import time
import json
from dataclasses import dataclass

from PySide6.QtCore import QObject, Signal, Slot
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
from PySide6.QtWidgets import QPushButton, QLabel

from Store import Store

# ----------------------------------------------------------------------------
#   A few classes to store sig info, exploring dataclasses.

@dataclass
class SigData:
    signal: object
    caller: str

@dataclass
class SlotData:
    slot: object
    fcn: str
    caller: str

@dataclass
class ConnData:
    # signal_name: str
    slot_name: str
    caller: str

# ----------------------------------------------------------------------------

class SigMan(QObject):                              

    # ----------------------------------------------------------------
    #   This is a singleton class.

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    # ----------------------------------------------------------------
    #   Although singleton class, guard used here because __init__() is called for each instance.
    #   Only want to initialize once but not in __new__().

    def __init__(self):
        if hasattr( self, '_initialized' ):
            return
        self._initialized = True
        super().__init__()

        self.verbose = False
        self.signals = {}           # indexed by signal_name
        self.slots = {}             # indexed by slot_name
        self.connections = {}       # indexed by signal_name
        self.widgets = {}           # indexed by signal_name, widget, if any, associated with signal.
        self.record = None
        self.rfd = None

    # ----------------------------------------------------------------
    # caller = inspect.stack()[1].function
    #   WRW 4-Apr-2025 - Add widget arg to register_signal(), populate calls gradually.
    #   It is the widget, if any, that is associated with the signal. For use by inspect()
    #   on shift-left-click.

    def register_signal( self, signal_name, signal, widget=None ):

        if signal_name in self.signals:
            raise ValueError(f"ERROR: At register_signal() '{signal_name}' already registered" )

        # ----------------------------
        frame = inspect.currentframe().f_back  # Get caller frame
        caller_name = frame.f_code.co_name  # Function name
        caller_file = os.path.basename(frame.f_code.co_filename)
        caller_instance = frame.f_locals.get('self', None)
        caller_class = caller_instance.__class__.__name__ if caller_instance else None
        caller = f"{caller_file} -> {caller_class}().{caller_name}()" if caller_class else f"{caller_name}()"
        # ----------------------------

        if self.verbose:
            print( f"{'Register Signal:':16} {signal_name:45} {caller}" )

        self.signals[ signal_name ] = SigData( signal, caller )
        self.widgets[ widget ] = signal_name

    # ----------------------------------------------------------------

    def sig_registered( self, signal_name ):
        return True if signal_name in self.signals else False

    # ----------------------------------------------------------------
    #   Definitely do need an array here as can can have one slot name 
    #       bound to multiple slots. C.f. "slot_play_audio_starting".
    #   NO! Such binding is done with connections.
    #   WRW 17-Feb-2025 - Earlier brain fart - multiple slots per slot name.
    #       Corrected, now only one slot registration allowed.

    def register_slot(self, slot_name, slot):

        if slot_name in self.slots:
            raise ValueError(f"ERROR: At register_slot() '{slot_name}' already registered" )

        # ----------------------------
        frame = inspect.currentframe().f_back  # Get caller frame
        caller_name = frame.f_code.co_name  # Function name
        caller_file = os.path.basename(frame.f_code.co_filename)
        caller_instance = frame.f_locals.get('self', None)
        caller_class = caller_instance.__class__.__name__ if caller_instance else None
        caller = f"{caller_file} -> {caller_class}().{caller_name}()" if caller_class else f"{caller_name}()"
        # ----------------------------

        fcn_name = f"{slot.__name__}"
        fcn_sig = inspect.signature(slot)
        fcn = f"{fcn_name}{fcn_sig}"

        if self.verbose:
            print( f"{'Register Slot:':16} {slot_name:45} {fcn:35} {caller}" )

        self.slots[ slot_name ] = SlotData( slot, fcn, caller )

    # ----------------------------------------------------------------

    def connect(self, signal_name, slot_name):
        # ----------------------------
        frame = inspect.currentframe().f_back  # Get caller frame
        caller_name = frame.f_code.co_name  # Function name
        caller_file = os.path.basename(frame.f_code.co_filename)
        caller_instance = frame.f_locals.get('self', None)
        caller_class = caller_instance.__class__.__name__ if caller_instance else None
        caller = f"{caller_file} -> {caller_class}().{caller_name}()" if caller_class else f"{caller_name}()"
        # ----------------------------

        if signal_name not in self.signals:
            raise ValueError( f"ERROR: At connect(): Signal '{signal_name}' not registered.")

        if slot_name not in self.slots:
            raise ValueError(f"ERROR: At connect(): Slot '{slot_name}' not registered." )

        if self.verbose:
            print( f"{'Connect:':16} {signal_name} -> {slot_name}" )        # no caller here, all the same

        self.signals[ signal_name ].signal.connect( self.slots[ slot_name ].slot )                    # *** CONNECT

        self.connections.setdefault(signal_name, []).append(ConnData( slot_name, caller ))
    
    # ----------------------------------------------------------------

    def emit( self, signal_name, *args, **kwargs):

        if self.verbose:
            # ----------------------------
            frame = inspect.currentframe().f_back  # Get caller frame
            caller_name = frame.f_code.co_name  # Function name
            caller_file = os.path.basename(frame.f_code.co_filename)
            caller_instance = frame.f_locals.get('self', None)
            caller_class = caller_instance.__class__.__name__ if caller_instance else None
            caller = f"{caller_file}->{caller_class}().{caller_name}()" if caller_class else f"{caller_name}()"
            # ----------------------------

        if signal_name in self.signals:
            # /// maybe show later signal = self.signals[ signal_name ].signal

            if self.verbose:
                print( f"Emit: {signal_name:40} {caller}" )

            try:
                self.signals[ signal_name ].signal.emit(*args, **kwargs)            # *** EMIT

                if self.rfd:
                    self.do_record( signal_name, *args, **kwargs )

            except Exception:
                (extype, value, traceback) = sys.exc_info()
                raise ValueError( f"ERROR: emit() failed, type: {extype}, value: {value}" )

        else:
            raise ValueError( f"ERROR: At emit(): Signal '{signal_name}' not registered in SigMan.")
    
    # ----------------------------------------------------------------

    def get_info( self, widget ):
        if widget in self.widgets:
            res = []
            signal_name = self.widgets[ widget ]
            res.append( f"Signal: {signal_name}" )
            caller = self.signals[ signal_name ].caller
            res.append( f"Registered by: {caller}" )
            res.append( f"Connected to {len(self.connections[ signal_name ])} slot(s):")
            for connection in self.connections[ signal_name ]:
                fcn = self.slots[ connection.slot_name ].fcn
                res.append( f"    Slot: {connection.slot_name} -> {fcn}" )
            return '\n'.join( res )
        return None

    # ----------------------------------------------------------------
    #   Show signals, slots, and connections for development.

    def show( self ):
        res = []
        for signal_name in sorted( self.connections ):
            caller = self.signals[ signal_name ].caller
            res.append( f"{signal_name:45} {caller}" )

            for connection in self.connections[ signal_name ]:
                fcn = self.slots[ connection.slot_name ].fcn
                res.append( f"    {connection.slot_name:41} {fcn:35} {connection.caller}" )
            res.append( '' )

        # --------------------------------------------------------------------
        print( '-'*60 )
        print( "Registered signal count:", len( self.signals) )
        print( "Registered slot count:", len(self.slots ) )
        print( '' )

        # --------------------------------------------------------------------
        print( '-'*60 )
        print( "Connection count by signal:" )
        for signal_name in sorted( self.connections ):
            print( f"   {signal_name}: {len( self.connections[ signal_name ])}" )
        print( '' )

        # --------------------------------------------------------------------
        print( '-'*60 )
        print( "Connection by signal:" )
        print( '\n'.join( res ) )
        print( '' )

        # --------------------------------------------------------------------
        sigs_by_caller = {}
        for signal_name in self.signals:
            caller = self.signals[ signal_name ].caller
            sigs_by_caller.setdefault( caller, [] ).append( signal_name )

        print( '-'*60 )
        print( "Signal registration By caller:" )
        print( '' )
        for caller in sorted( sigs_by_caller ):
            print( f"  {caller}" )
            for sig in sigs_by_caller[ caller ]:
                print( f"    {sig}" )
            print( '' )
        print( '' )

        # --------------------------------------------------------------------
        slots_by_caller = {}
        for slot_name in self.slots:
            caller = self.slots[ slot_name ].caller
            slots_by_caller.setdefault( caller, [] ).append( slot_name )

        print( '-'*60 )
        print( "Slot registration By caller:" )
        print( '' )
        for caller in sorted( slots_by_caller ):
            print( f"  {caller}" )
            for slot in slots_by_caller[ caller ]:
                print( f"    {slot}" )
            print( '' )
        print( '' )

    # ----------------------------------------------------------------

    def set_verbose( self, verbose ):
        self.verbose = verbose

    # ============================================================================
    #   Record / Playback
    # ============================================================================

    def set_record( self, record ):
        s = Store()
        self.record = record
        self.start = time.time()

        try:
            rfd = open( record, 'w' )

        except Exception:
            (extype, value, traceback) = sys.exc_info()
            txt = f"ERROR, open record file '{record}' failed, type: '{extype}', value: '{value}'"
            s.msgWarn( txt )
            self.rfd = None

        else:
            self.rfd = rfd

    # ------------------------------------------

    def encode_bytesio(self, obj):
        import base64
        if hasattr(obj, 'read'):
            # Save current position
            pos = obj.tell()
            obj.seek(0)
            b64 = base64.b64encode(obj.read()).decode("ascii")
            obj.seek(pos)  # Restore position
            return {"__bytesio__": True, "base64": b64}
        return obj

    # ------------------------------------------

    def make_json_safe( self, obj ):
        from bl_tables import getDataNew

        if isinstance(obj, (int, float, str, bool, type(None))):
            return obj

        elif isinstance(obj, (list, tuple)):
            return [self.make_json_safe(i) for i in obj]

        elif isinstance(obj, dict):
            return {self.make_json_safe(k): self.make_json_safe(v) for k, v in obj.items()}

        elif isinstance(obj, bytes):
            return obj.decode("utf-8", errors="replace")  # or base64 if binary

        elif hasattr(obj, 'read'):  # likely BytesIO or file-like
            return self.encode_bytesio(obj)

        # Convert to a dict with a marker for later decoding
        elif hasattr(obj, "__dict__") and isinstance(obj, getDataNew):
            return {
                "__getdatanew__": True,
                "attributes": self.make_json_safe(obj.__dict__)
            }

        else:
            return str(obj)

    # ------------------------------------------
    
    def do_record( self, signal_name, *args, **kwargs ):
        now = time.time()
        delta = now - self.start
        self.start = now

        r = { 'delta' : delta, 
              'signal_name' :   signal_name,
              'args' :          self.make_json_safe( args ),
              'kwargs' :        self.make_json_safe( kwargs ),
              'timestamp' :     now,
            }

        self.rfd.write( json.dumps( r ) + '\n')
        self.rfd.flush()

    # ------------------------------------------

    def load_signal_log( self, path):
        with open(path, "r", encoding="utf-8") as f:
            for line in f:
                yield json.loads(line)

    # ------------------------------------------
    
    def decode_bytesio( self, obj ):
        from io import BytesIO
        import base64

        if isinstance(obj, dict) and obj.get("__bytesio__"):
            raw = base64.b64decode(obj["base64"])
            return BytesIO(raw)
        return obj

    # ------------------------------------------

    def unsanitize( self, obj ):
        from io import BytesIO
        import base64
        from bl_tables import getDataNew
        self.odata = None

        # Handle dicts with special serialization tags
        if isinstance(obj, dict):
            if obj.get("__bytesio__"):
                # Restore BytesIO from base64-encoded string
                raw = base64.b64decode(obj["base64"])
                self.otype = 'BytesIO'
                return BytesIO(raw)
    
            elif obj.get("__getdatanew__"):
                instance = getDataNew.__new__(getDataNew)
                instance.__dict__.update(self.unsanitize(obj["attributes"]))
                self.otype = 'getDataNew'
                return instance
    
            elif False and obj.get("__custom__"):
                clsname = obj["class"]
                from your_module import CLASS_REGISTRY  # if you're using one
                cls = CLASS_REGISTRY.get(clsname)
                if cls:
                    instance = cls.__new__(cls)
                    instance.__dict__.update(self.unsanitize(obj["attributes"]))
                    return instance
    
            # If not a special object, recurse into the dict
            self.otype = 'dict'
            return {k: self.unsanitize(v) for k, v in obj.items()}
    
        elif isinstance(obj, list):
            self.otype = 'list'
            return [self.unsanitize(i) for i in obj]
    
        else:
            self.otype = str( type( obj ) )
            self.odata = obj
            return obj

    def get_otype( self ):
        return self.otype

    def get_odata( self ):
        return self.odata

    # ------------------------------------------

    def schedule_replay( self, records, index = 0 ):
        from PyQt6.QtCore import QTimer
        s = Store()

        if index >= len( records ):
            return

        record = records[ index ]

        delta = int(record['delta'] * 1000)
        signal_name = record["signal_name"]

        args = self.unsanitize( record.get("args", [] ))
        aotype = self.get_otype()
        aodata = self.get_odata()

        kwargs = self.unsanitize( record.get("kwargs", {} ))
        kotype = self.get_otype()
        kodata = self.get_odata()

        print(f"{signal_name:>35}: {aotype:20} {len(args):3}, {kotype:>10} {len(kwargs):3}, {delta:6} ms")
        if aodata:
            print( f"{' '*36} {aodata}" )

        def emit_and_schedule_next():
            s.sigman.emit( signal_name, *args, **kwargs )
            self.schedule_replay( records, index + 1)

        QTimer.singleShot( delta, emit_and_schedule_next )


    def do_playback(self, path):
        s = Store()
        records = []

        for record in self.load_signal_log(path):
            records.append( record )

        self.schedule_replay( records )


# ============================================================================
#   Unit Tests
# ============================================================================

class Sender1(QWidget):
    sig_s1 = Signal( str )

    def __init__(self, txt ):
        super().__init__()
        s = Store()
        self.txt = txt
        s.sigman.register_signal( "sig_s1", self.sig_s1 )
        self.setWindowTitle("Widget 1")
        self.layout = QVBoxLayout()
        self.button = QPushButton("S1 Send Text")
        self.layout.addWidget(self.button)
        self.setLayout(self.layout)
        
        #   Inside the object we connect widget signals to internal handlers.

        self.button.clicked.connect(self.send_message)
    
    #   And then the internal handler emits a registered signal.

    def send_message(self):
        s.sigman.emit( 'sig_s1', f"Hello from Sender 1, {self.txt} instance")

# ----------------------------------------------------------------------------

class Sender2(QWidget):
    sig_s2 = Signal( int )

    def __init__(self, val ):
        super().__init__()
        s = Store()
        self.val = val
        s.sigman.register_signal( "sig_s2", self.sig_s2 )
        self.setWindowTitle("Widget 1")
        self.layout = QVBoxLayout()
        self.button = QPushButton("S2 Send Integer")
        self.layout.addWidget(self.button)
        self.setLayout(self.layout)
        
        #   Inside the object we connect widget signals to internal handlers.

        self.button.clicked.connect(self.send_message)
    
    #   And then the internal handler emits a registered signal.

    def send_message(self):
        s.sigman.emit( 'sig_s2', self.val )

# ----------------------------------------------------------------------------

class Receiver1(QWidget):
    def __init__(self):
        super().__init__()
        s = Store()
        
        self.setWindowTitle("Widget 2")
        self.layout = QVBoxLayout()
        self.label = QLabel("R1 Waiting for message...")
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)
        
        # Register the slot dynamically
        s.sigman.register_slot( 'slot_r1', self.receive_message)
    
    # Update the label with the received message

    @Slot( str )
    def receive_message(self, txt):
        self.label.setText( f"R1 received: {txt}" )

# ----------------------------------------------------------------------------

class Receiver2(QWidget):
    def __init__(self):
        super().__init__()
        s = Store()
        
        self.setWindowTitle("Widget 3")
        self.layout = QVBoxLayout()
        self.label = QLabel("R2 Waiting for message...")
        self.layout.addWidget(self.label)
        self.setLayout(self.layout)
        
        # Register the slot dynamically
        s.sigman.register_slot( 'slot_r2', self.receive_message)
    
    # Update the label with the received message

    @Slot( int )
    def receive_message(self, val ):
        self.label.setText( f"R2 received: {val}" )

# ----------------------------------------------------------------------------

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        
        self.setWindowTitle("Enhanced Signal-Slot Example")

        central_widget = QWidget()
        layout = QVBoxLayout()
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        w = Sender1( "w1" )     # Create widgets
        layout.addWidget(w)

        # w = Sender1( "w2" )
        # layout.addWidget(w)

        # w = Sender1( "w3" )
        # layout.addWidget(w)

        w = Sender2( 100 )
        layout.addWidget(w)

        # w = Sender2( 200 )
        # layout.addWidget(w)

        # w = Sender2( 300 )
        # layout.addWidget(w)

        w = Receiver1(  )
        layout.addWidget(w)

        w = Receiver2(  )
        layout.addWidget(w)

        s.sigman.connect( 'sig_s1', 'slot_r1' )
        s.sigman.connect( 'sig_s1', 'slot_r2' )
        s.sigman.connect( 'sig_s2', 'slot_r1' )
        s.sigman.connect( 'sig_s2', 'slot_r2' )
        s.sigman.show()

# ----------------------------------------------------------------------------

if __name__ == "__main__":
    from bl_unit_test import UT
    from bl_style import StyleSheet

    s = UT()

    s.app = QApplication(sys.argv)
    s.app.setStyleSheet( StyleSheet )   # OK, unit test
    window = MainWindow()
    window.show()
    sys.exit(s.app.exec())

# ----------------------------------------------------------------------------
