
import sys
import os
import functools

from gi.repository import Gtk
from gi.repository import Pango

from .config import Config
from .filelist import FileListStore, FileListView
from .infoview import InfoView


class TVRenamer(Gtk.Window):

    def __init__(self):
        super(TVRenamer, self).__init__()

        self.config = Config()
        self.config.load()

        self.set_title('TV Series Renamer')
        self.connect('destroy', self.quit)
        self.resize(self.config.width, self.config.height)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect('configure-event', self.on_configure_event)

        vbox = Gtk.VBox(False, 12)
        self.add(vbox)
        vbox.set_border_width(12)

        # Regex combo box
        hbox = Gtk.HBox(False, 6)
        vbox.pack_start(hbox, False, False)
        hbox.pack_start(Gtk.Label('Regex:', True, True, 0), False, False)
        regex_store = Gtk.ListStore(str)
        for regex in self.config.regexes:
            regex_store.append([regex])
        regex = Gtk.ComboBoxEntry(regex_store)
        regex.get_child().modify_font(Pango.FontDescription("monospace 10"))
        hbox.pack_start(regex, True, True, 0)
        extract = Gtk.Button('Extract Info')
        hbox.pack_start(extract, False, False)
        def on_extract(*args):
            self.extract_info()
            self.update_previews()
            self.update_info()
        extract.connect('clicked', on_extract)
        self.regex_store, self.regex = regex_store, regex

        # List
        paned = Gtk.HPaned()
        vbox.pack_start(paned, True, True, 0)

        sw = Gtk.ScrolledWindow()
        paned.pack1(sw)
        sw.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        print sys.argv
        files = [filename for filename in sys.argv[1:] if os.path.isfile(filename)]
        self.filelist_model = FileListStore(files)
        self.filelist_view = FileListView(self.filelist_model)
        self.filelist_view.set_size_request(300, -1)
        self.filelist_view.get_selection().connect('changed', self.update_info)
        sw.add(self.filelist_view)

        sw = Gtk.ScrolledWindow()
        paned.pack2(sw, False, False)
        sw.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        self.info_view = InfoView()
        self.info_view.set_size_request(100, -1)
        self.info_view.connect('info-changed', self.update_previews)
        sw.add(self.info_view)

        # Template combo box
        hbox = Gtk.HBox(False, 6)
        vbox.pack_start(hbox, False, False)
        hbox.pack_start(Gtk.Label('Template:', True, True, 0), False, False)
        template_store = Gtk.ListStore(str)
        for template in self.config.templates:
            template_store.append([template])
        template = Gtk.ComboBoxEntry(template_store)
        hbox.pack_start(template, True, True, 0)
        template.get_child().modify_font(Pango.FontDescription("monospace 10"))
        template.connect('changed', self.update_previews)
        self.template_store, self.template = template_store, template

        # Destination folder
        hbox = Gtk.HBox(False, 6)
        vbox.pack_start(hbox, False, False)
        hbox.pack_start(Gtk.Label('Destination Folder:', True, True, 0), False, False)
        dialog = Gtk.FileChooserDialog('Select destination',
                                       action=Gtk.FileChooserAction.SELECT_FOLDER,
                                       buttons=('Cancel', Gtk.ResponseType.CANCEL,
                                                'Select', Gtk.ResponseType.ACCEPT))
        self.destination = Gtk.FileChooserButton(dialog)
        self.destination.set_filename(self.config.destination)
        def on_destination_changed(button):
            self.config.destination = button.get_filename()
        self.destination.connect('file-set', on_destination_changed)
        hbox.pack_start(self.destination, False, False)
        
        # Rename button
        rename = Gtk.Button('Rename')
        vbox.pack_start(rename, False, False)
        rename.connect('clicked', self.rename)

        self.show_all()

    def run(self):
        Gtk.main()

    def quit(self, *args):
        Gtk.main_quit()
        self.config.save()

    def get_regex(self):
        iter = self.regex.get_active_iter()
        if iter:
            return self.regex_store.get_value(iter, 0)
        else:
            return self.regex.get_child().get_text()

    def get_template(self):
        iter = self.template.get_active_iter()
        if iter:
            return self.template_store.get_value(iter, 0)
        else:
            return self.template.get_child().get_text()

    def extract_info(self, *args):
        self.filelist_model.extract_info_all(self.get_regex())

    def update_previews(self, *args):
        self.filelist_model.render_preview_all(self.get_template())

    def update_info(self, *args):
        selection = self.filelist_view.get_selection()
        model, selected = selection.get_selected_rows()
        if not selected:
            self.info_view.clear_info()
        else:
            iter = model.get_iter(selected[0])
            info = model.get_value(iter, model.COLUMN_FILEINFO)
            self.info_view.set_info(info)

    def rename(self, *args):
        self.filelist_model.rename(self.config.destination)

    def on_cell_edited(self, cell, path, new_text, column):
        if column == self.EPISODE_COL:
            try:
                episode = int(new_text)
            except ValueError:
                episode = 0
            self.store[path][column] = episode
            model, selected = self.tree_view.get_selection().get_selected_rows()
            iters = [model.get_iter(path) for path in selected]
            for iter in iters:
                model.set(iter, column, episode)
                episode += 1
        else:
            self.store[path][column] = new_text

    def on_configure_event(self, widget, event):
        self.config.width, self.config.height = event.width, event.height
        