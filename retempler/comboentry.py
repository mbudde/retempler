
from gi.repository import Gtk
from gi.repository import Pango


class ComboBoxEntryEdit(Gtk.ComboBoxEntry):

    def __init__(self, config, configvar):
        model = Gtk.ListStore(str)
        for value in config[configvar]:
            model.append([value])

        super(ComboBoxEntryEdit, self).__init__(model=model, text_column=0)
        self.get_child().modify_font(Pango.FontDescription("monospace 10"))

        def save_entries(*args):
            config[configvar] = [row[0] for row in self.get_model()]
        model.connect('row-changed', save_entries)
        model.connect('row-deleted', save_entries)

    def get_wrapped(self, label):
        hbox = Gtk.HBox(homogeneous=False, spacing=6)
        hbox.pack_start(Gtk.Label(label=label), False, False, 0)

        hbox.pack_start(self, True, True, 0)

        add_img = Gtk.Image.new_from_stock(Gtk.STOCK_ADD, Gtk.IconSize.BUTTON)
        add_entry = Gtk.Button(image=add_img)
        hbox.pack_start(add_entry, False, False, 0)
        def on_add_entry(button):
            iter = self.get_active_iter()
            if not iter:
                text = self.get_active_text()
                if text:
                    self.get_model().append([text])
        add_entry.connect('clicked', on_add_entry)

        delete_img = Gtk.Image.new_from_stock(Gtk.STOCK_REMOVE, Gtk.IconSize.BUTTON)
        delete_entry = Gtk.Button(image=delete_img)
        hbox.pack_start(delete_entry, False, False, 0)
        def on_delete_entry(button):
            iter = self.get_active_iter()
            if iter:
                self.get_model().remove(iter)
        delete_entry.connect('clicked', on_delete_entry)

        return hbox

    def get_active_text(self):
        iter = self.get_active_iter()
        if iter:
            return self.get_model().get_value(iter, 0)
        else:
            return self.get_child().get_text()
