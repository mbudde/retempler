
import sys
import os
import functools

import gi
gi.require_version('Gtk', '2.0')
from gi.repository import Gtk

from .config import Config
from .filelist import FileListStore, FileListView
from .infoview import InfoView
from .comboentry import ComboBoxEntryEdit

class Retempler(Gtk.Window):

    def __init__(self):
        super(Retempler, self).__init__()

        self.config = Config()
        self.config.load()

        self.set_title('Retempler')
        self.connect('destroy', self.quit)
        self.resize(self.config.width, self.config.height)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.connect('configure-event', self.on_configure_event)

        vbox = Gtk.VBox(homogeneous=False, spacing=12)
        self.add(vbox)
        vbox.set_border_width(12)

        # Regex combo box
        self.regex = ComboBoxEntryEdit(self.config, 'regexes')
        hbox = self.regex.get_wrapped('Regex:')
        vbox.pack_start(hbox, False, False, 0)

        extract = Gtk.Button('Extract Info')
        hbox.pack_start(extract, False, False, 0)
        def on_extract(*args):
            self.extract_info()
            self.update_previews()
            self.update_info()
        extract.connect('clicked', on_extract)

        # List
        paned = Gtk.HPaned()
        vbox.pack_start(paned, True, True, 0)

        sw = Gtk.ScrolledWindow()
        paned.pack1(sw)
        sw.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        sw.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)

        files = []
        for path in (os.path.realpath(path) for path in sys.argv[1:]):
            if os.path.isdir(path):
                dirfiles = (os.path.join(path, name) for name in os.listdir(path))
                files.extend(name for name in dirfiles if os.path.isfile(name))
            elif os.path.isfile(path):
                files.append(path)

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
        self.template = ComboBoxEntryEdit(self.config, 'templates')
        self.template.connect('changed', self.update_previews)
        hbox = self.template.get_wrapped('Template:')
        vbox.pack_start(hbox, False, False, 0)

        # Destination folder
        hbox = Gtk.HBox(homogeneous=False, spacing=6)
        vbox.pack_start(hbox, False, False, 0)
        hbox.pack_start(Gtk.Label(label='Destination Folder:'), False, False, 0)
        dialog = Gtk.FileChooserDialog(title='Select destination',
                                       action=Gtk.FileChooserAction.SELECT_FOLDER,
                                       buttons=('Cancel', Gtk.ResponseType.CANCEL,
                                                'Select', Gtk.ResponseType.ACCEPT))
        self.destination = Gtk.FileChooserButton(dialog=dialog)
        if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]):
            self.destination.set_filename(sys.argv[1])
        else:
            self.destination.set_filename(self.config.destination)
        def on_destination_changed(button):
            self.config.destination = button.get_filename()
        self.destination.connect('file-set', on_destination_changed)
        hbox.pack_start(self.destination, False, False, 0)
        
        # Rename button
        rename = Gtk.Button(label='Rename')
        vbox.pack_start(rename, False, False, 0)
        rename.connect('clicked', self.rename)

        self.show_all()

    def run(self):
        Gtk.main()

    def quit(self, *args):
        Gtk.main_quit()
        self.config.save()

    def extract_info(self, *args):
        self.filelist_model.extract_info_all(self.regex.get_active_text())

    def update_previews(self, *args):
        self.filelist_model.render_preview_all(self.template.get_active_text())

    def update_info(self, *args):
        selection = self.filelist_view.get_selection()
        model, selected = selection.get_selected_rows()
        if not selected:
            self.info_view.clear_info()
        else:
            iters = [model.get_iter(path) for path in selected]
            info_objs = [model.get_value(iter, model.COLUMN_FILEINFO)
                         for iter in iters]
            self.info_view.set_info(info_objs)

    def rename(self, *args):
        self.filelist_model.rename(self.destination.get_filename())

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
        
