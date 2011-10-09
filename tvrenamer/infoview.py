
from gi.repository import Gtk
from gi.repository import GObject


class InfoView(Gtk.TreeView):

    __gsignals__ = {
        'info-changed': (GObject.SignalFlags.RUN_LAST, None, (object, object)),
    }

    (COLUMN_KEY,
     COLUMN_VALUE) = range(2)

    def __init__(self):
        super(InfoView, self).__init__()
        self.info = None
        # self.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)
        # self.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        # self.connect('key-press-event', self.on_keypress)

        cell = Gtk.CellRendererText()
        cell.set_property('editable', True)
        cell.connect('edited', self.on_cell_edited, self.COLUMN_KEY)
        column = Gtk.TreeViewColumn('Key', cell, text=self.COLUMN_KEY)
        column.set_sort_column_id(self.COLUMN_KEY)
        column.set_resizable(True)
        self.append_column(column)

        cell = Gtk.CellRendererText()
        cell.set_property('editable', True)
        cell.connect('edited', self.on_cell_edited, self.COLUMN_VALUE)
        column = Gtk.TreeViewColumn('Value', cell, text=self.COLUMN_VALUE)
        column.set_sort_column_id(self.COLUMN_VALUE)
        column.set_resizable(True)
        self.append_column(column)

    def set_info(self, info):
        self.info = info
        model = Gtk.ListStore(str, str)
        model.set_sort_column_id(self.COLUMN_KEY, Gtk.SortType.ASCENDING)
        model.connect('row-changed', self.on_model_changed)
        for key, value in info.iteritems():
            model.append([key, str(value)])
        model.append([None, None])
        self.set_model(model)

    def clear_info(self):
        self.info = None
        self.set_model(None)

    def on_cell_edited(self, cell, path, new_text, column):
        model = self.get_model()
        if column == self.COLUMN_KEY:
            if new_text in self.info:
                return
            old_key = model[path][column]
            if not new_text:
                if not old_key:
                    return
                iter = model.get_iter(path)
                model.remove(iter)
                if old_key:
                    del self.info[old_key]
                return
            if old_key is None:
                value = model[path][self.COLUMN_VALUE]
                self.info[new_text] = value
                model.append([None, None])
            else:
                value = self.info.pop(old_key)
                self.info[new_text] = value
            model[path][column] = new_text
        else:
            key = model[path][self.COLUMN_KEY]
            if key is not None:
                self.info[key] = new_text
            model[path][column] = new_text

    def on_model_changed(self, model, path, *args):
        self.emit('info-changed', self, path)
