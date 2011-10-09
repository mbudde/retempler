
from gi.repository import Gtk
from gi.repository import GObject


class InfoView(Gtk.TreeView):

    __gsignals__ = {
        'info-changed': (GObject.SignalFlags.RUN_LAST, None, (object, object)),
    }

    (COLUMN_KEY,
     COLUMN_VALUE,
     COLUMN_KEY_FORMATTED) = range(3)

    def __init__(self):
        super(InfoView, self).__init__()
        self.info = None
        # self.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)
        # self.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        # self.connect('key-press-event', self.on_keypress)

        cell = Gtk.CellRendererText()
        cell.set_property('editable', True)
        cell.connect('edited', self.on_cell_edited, self.COLUMN_KEY)
        column = Gtk.TreeViewColumn('Key', cell, markup=self.COLUMN_KEY_FORMATTED)
        column.set_sort_column_id(100)
        column.set_resizable(True)
        self.append_column(column)

        cell = Gtk.CellRendererText()
        cell.set_property('editable', True)
        cell.connect('edited', self.on_cell_edited, self.COLUMN_VALUE)
        column = Gtk.TreeViewColumn('Value', cell, text=self.COLUMN_VALUE)
        column.set_sort_column_id(self.COLUMN_VALUE)
        column.set_resizable(True)
        self.append_column(column)

    def set_info(self, info_objs):
        self.info_objs = info_objs
        model = Gtk.ListStore(str, str, str)
        model.set_sort_func(100, self.sort_rows_by_key)
        model.set_sort_column_id(100, Gtk.SortType.ASCENDING)
        merged_info = {}
        for info in info_objs:
            for key, value in info.iteritems():
                if key in merged_info:
                    if merged_info[key] != (str(value), False):
                        merged_info[key] = ('...', True)
                else:
                    merged_info[key] = (str(value), False)
        for key, value in merged_info.iteritems():
            val, diff = value
            if diff:
                model.append([key, val, '<i>' + key + '</i>'])
            else:
                model.append([key, val, key])
        model.connect('row-changed', self.on_model_changed)
        model.append([None, None, None])
        self.set_model(model)

    def clear_info(self):
        self.info = None
        self.set_model(None)

    def on_cell_edited(self, cell, path, new_text, column):
        model = self.get_model()
        iter = model.get_iter(path)
        if column == self.COLUMN_KEY:
            for info in self.info_objs:
                if new_text in info:
                    # key already exist
                    return
            old_key = model.get_value(iter, column)
            if new_text == old_key:
                # nothing changed
                return
            if not new_text:
                # remove key
                model.remove(iter)
                for info in self.info_objs:
                    if old_key and old_key in info:
                        del info[old_key]
                return
            if old_key is None:
                # insert new key
                value = model.get_value(iter, self.COLUMN_VALUE)
                if value is None:
                    value = ''
                for info in self.info_objs:
                    info[new_text] = value
                model.append([None, None, None])
            else:
                # rename key
                for info in self.info_objs:
                    if old_key in info:
                        value = info.pop(old_key)
                        info[new_text] = value
            model.set_value(iter, column, new_text)
            model.set_value(iter, self.COLUMN_KEY_FORMATTED, new_text)
        else:
            key = model.get_value(iter, self.COLUMN_KEY)
            print 'changing value for key', key
            if key is not None:
                for info in self.info_objs:
                    info[key] = new_text
            model.set_value(iter, column, new_text)
            model.set_value(iter, self.COLUMN_KEY_FORMATTED, key)

    def on_model_changed(self, model, path, *args):
        self.emit('info-changed', self, path)

    def sort_rows_by_key(self, model, iter1, iter2, user_data):
        key1 = model.get_value(iter1, self.COLUMN_KEY)
        key2 = model.get_value(iter2, self.COLUMN_KEY)
        if key1 == key2:
            return 0
        elif key1 is None:
            return 1
        elif key2 is None:
            return -1
        else:
            return cmp(key1, key2)
