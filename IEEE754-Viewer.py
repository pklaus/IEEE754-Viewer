#!/usr/bin/env python
# -*- encoding: UTF8 -*-

# author: Philipp Klaus, philipp.l.klaus AT web.de


#   This file is part of IEEE754-Viewer.
#
#   IEEE754-Viewer is free software: you can redistribute it and/or modify
#   it under the terms of the GNU General Public License as published by
#   the Free Software Foundation, either version 3 of the License, or
#   (at your option) any later version.
#
#   IEEE754-Viewer is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU General Public License for more details.
#
#   You should have received a copy of the GNU General Public License
#   along with IEEE754-Viewer.  If not, see <http://www.gnu.org/licenses/>.

import gtk
import signal
import sys
import os

PROGRAM_ICON = 'icon.png'

def getAbsoluteFilepath(filename):
    fullpath = os.path.abspath(os.path.dirname(sys.argv[0]))
    return fullpath + '/' + filename


class IEEE754Viewer(gtk.Window):
    def __init__(self, app_controller, precision = 32, initial_value = 0.0):
        gtk.Window.__init__(self,gtk.WINDOW_TOPLEVEL)
        self.set_title("IEEE754 Viewer")
        self.set_icon_from_file(getAbsoluteFilepath(PROGRAM_ICON))
        #self.set_default_size(500, 200)
        self.connect('destroy', gtk.main_quit)
        self.app_controller = app_controller
        
        spacing, homogeneous, expand, fill, padding = 2, True, True, True, 5
        
        label1 = gtk.Label('Enter a Decimal Floating Point:')
        self.input_entry = gtk.Entry()
        self.input_entry.connect('changed', self.decimal_changed)
        input_hbox = gtk.HBox(homogeneous, spacing)
        input_hbox.pack_start(label1, expand, fill, padding)
        input_hbox.pack_start(self.input_entry, expand, fill, padding)
        
        
        mode_radio_button = dict()
        mode_radio_button[32] = gtk.RadioButton(None, "32 bit precision")
        mode_radio_button[64] = gtk.RadioButton(mode_radio_button[32], "64 bit precision")

        mode_radio_button[precision].set_active(True)
        
        mode_radio_button[32].connect("toggled", self.mode_change, 32)
        mode_radio_button[64].connect("toggled", self.mode_change, 64)

        mode_radio_box = gtk.VBox(homogeneous, spacing)
        mode_radio_box.pack_start(mode_radio_button[32], expand, fill, padding)
        mode_radio_box.pack_start(mode_radio_button[64], expand, fill, padding)
        
        self.representation_label = gtk.Label()
        
        middle_box = gtk.HBox(False, spacing)
        middle_box.pack_start(mode_radio_box, False, False, padding)
        #                                                expand, fill, padding
        middle_box.pack_start(self.representation_label, True, True, padding)
        
        self.precision = precision
        
        if self.precision == 32:
            self.exp_bits = 8
        elif self.precision == 64:
            self.exp_bits = 11
        self.bias = (2**(self.exp_bits-1))-1
        self.max_exponent = self.bias
        self.mantissa_bits = self.precision -1 - self.exp_bits
        
        representation_table = gtk.Table(self.precision+2,5)
        row = 0
        label = gtk.Label('bits...')
        representation_table.attach(label,0,self.precision+2,row,row+1)
        row += 1
        self.place_dummies(representation_table,row)
        for i in range(self.precision):
            label = gtk.Label(str(i))
            self.place(label,representation_table,i,row)
        row += 1
        self.bit=[]
        for i in range(self.precision):
            self.bit.append(gtk.CheckButton())
            self.place(self.bit[i],representation_table,i,row)
        row += 1
        label = gtk.Label('sign')
        representation_table.attach(label,0,1,row,row+1)
        label = gtk.Label('exponent')
        representation_table.attach(label,2,2+self.exp_bits,row,row+1)
        label = gtk.Label('mantissa')
        representation_table.attach(label,3+self.exp_bits,3+self.precision,row,row+1)
        row += 1
        self.sign_entry = gtk.Entry()
        self.sign_entry.set_width_chars(1)
        self.sign_entry.set_text('+')
        representation_table.attach(self.sign_entry,0,1,row,row+1)
        self.exp_entry = gtk.Entry()
        representation_table.attach(self.exp_entry,2,2+self.exp_bits,row,row+1)
        self.mantissa_entry = gtk.Entry()
        representation_table.attach(self.mantissa_entry,3+self.exp_bits,3+self.precision,row,row+1)
        
        homogeneous = False
        vbox = gtk.VBox(homogeneous, spacing)
        vbox.pack_start(input_hbox, expand, fill, padding)
        vbox.pack_start(middle_box, expand, fill, padding)
        vbox.pack_start(representation_table, expand, fill, padding)
        
        bin = gtk.Frame()
        bin.set_border_width(3)
        bin.set_shadow_type(gtk.SHADOW_NONE)
        bin.add(vbox)
        
        frame = gtk.Frame()
        frame.add(bin)
        frame.set_label("Binary Floating Point Formats according to the IEEE Standard for Floating-Point Arithmetic")
        frame.set_shadow_type(gtk.SHADOW_OUT)
        frame.set_border_width(5)
        
        
        self.add(frame)
        
        self.enter(initial_value)
        

    def mode_change(self, widget, change_to):
        self.app_controller.set_start_again(change_to, self.value, self.get_position())
        gtk.main_quit()

    def place(self, widget, table, bit, row):
        pos = self.precision -1 -bit + (1 if bit < self.precision-1 else 0) + (1 if bit < self.precision-self.exp_bits-1 else 0)
        table.attach(widget,pos,pos+1,row,row+1)

    def decimal_changed(self, widget):
        user_input = self.input_entry.get_text()
        if user_input == '' or user_input == '-':
            return
        try:
            self.value = float(self.input_entry.get_text())
        except Exception, error:
            self.print_status("%s is not a valid floating point." % self.input_entry.get_text())
            return
        self.print_status('actual representation: ' + repr(self.value))
        if self.value < 0:
            self.set_sign(-1)
        else:
            self.set_sign(1)
        self.abs_value = abs(self.value)
        
        (self.normalized_mantissa, self.exponent) = self.__calculate_normalized_mantissa_and_exponent(self.abs_value)
        
        self.exp_entry.set_text("%d - %d = %d" % (self.exponent,self.bias,self.exponent-self.bias))
        
        i = 0
        for bit in self.list_from_exponent(self.exponent):
            self.bit[self.precision - self.exp_bits - 1 + i].set_active(bit)
            i += 1
        
        mantissa_decimal = 1. # hidden bit
        for i in range(self.precision - self.exp_bits - 1):
            self.bit[self.mantissa_bits-i-1].set_active(self.normalized_mantissa[i+1])
            mantissa_decimal += 2.**(-(i+1)) if self.normalized_mantissa[i+1] else 0.
            #print "bit %d: %s" % (i, self.normalized_mantissa[i])
        #print "bit %d: %s" % (23, self.normalized_mantissa[23])
        
        self.mantissa_entry.set_text("Decimal value of the mantissa: %.16f" % mantissa_decimal)
            

    def __calculate_normalized_mantissa_and_exponent(self, abs_value):
        if abs_value < 0:
            raise Exception('The parameter abs_value has to be a positive real.')
        
        # calculate the mantissa
        self.trunk = int(self.abs_value)
        left_bits = []
        exponent_decimal = -1
        while self.trunk != 0:
            if exponent_decimal == self.max_exponent:
                return ([False for i in range(self.precision-1-self.exp_bits)],2**self.exp_bits-1) # infinity
            exponent_decimal += 1
            left_bits.append(self.trunk%2 == 1)
            self.trunk /= 2
        
        right_bits = []
        self.fraction = self.abs_value - int(self.abs_value)

        # for small numbers like 0.025, find beginning of significat bits
        if len(left_bits)==0:
            exponent_decimal = -1
            while self.fraction * 2 < 1:
                exponent_decimal -= 1
                self.fraction *= 2
                if exponent_decimal == -self.bias:
                    break
        
        while len(left_bits) + len(right_bits) < self.mantissa_bits + 1: # precision - sign - exponent
            right_bits.append(self.fraction * 2 >= 1)
            self.fraction = self.fraction * 2 if self.fraction*2<1 else self.fraction * 2-1.0
        
        
        
        # normalize the mantissa:
        left_bits.reverse()
        normalized_mantissa = left_bits[0:self.mantissa_bits+1]
        normalized_mantissa.extend(right_bits)
        
        exponent_decimal += self.bias
        return (normalized_mantissa, exponent_decimal)

    def list_from_exponent(self, exponent_decimal=0):
        # create a list of the bits for the exponent:
        exponent = []
        while len(exponent)<self.exp_bits:
            exponent.append(exponent_decimal%2 == 1)
            exponent_decimal = exponent_decimal/2
        return exponent

    def set_sign(self, sign):
        if sign == 1:
            self.sign_entry.set_text('+')
            self.bit[self.precision-1].set_active(False)
        elif sign == -1:
            self.bit[self.precision-1].set_active(True)
            self.sign_entry.set_text('-')
        else:
            self.sign_entry.set_text('')

    def print_status(self, status = 'internal representation'):
        self.representation_label.set_text('\n%s\n' % status)

    def place_dummies(self, table, row):
        spacer_text = '    '
        table.attach(gtk.Label(spacer_text),1,2,row,row+1)
        table.attach(gtk.Label(spacer_text),self.exp_bits+2,self.exp_bits+3,row,row+1)

    def enter(self,value):
        self.input_entry.set_text(str(value))


class Application_Handler(object):
    def __init__(self):
        self.start_again = True
        self.mode = 64
        self.value = 1.0
        while self.start_again:
            ieeeviewer = IEEE754Viewer(self, self.mode, self.value)
            try:
                ieeeviewer.move(self.coordinates[0],self.coordinates[1])
            except:
                pass
            ieeeviewer.show_all()
            self.start_again = False
            gtk.main()
            ieeeviewer.hide()
    
    def set_start_again(self, mode, value, old_window_position):
        self.start_again = True
        self.mode = mode
        self.value = value
        self.coordinates = old_window_position


def main():
    app_handler = Application_Handler()


if __name__ == "__main__":
    signal.signal(signal.SIGINT, signal.SIG_DFL) # ^C exits the application
    
    main()

