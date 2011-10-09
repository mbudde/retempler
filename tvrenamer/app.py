
import sys
import gtk
import pango
import os
import re
import shutil
import functools

from .config import Config
from .filelist import FileListStore, FileListView
from .infoview import InfoView


class TVRenamer(gtk.Window):

    def __init__(self):
        super(TVRenamer, self).__init__()

        self.config = Config()
        self.config.load()

        self.set_title('TV Series Renamer')
        self.connect('destroy', self.quit)
        self.resize(self.config.width, self.config.height)
        self.set_position(gtk.WIN_POS_CENTER)
        self.connect('configure-event', self.on_configure_event)

        vbox = gtk.VBox(False, 12)
        vbox.set_border_width(12)

        # Regex combo box
        hbox = gtk.HBox(False, 6)
        vbox.pack_start(hbox, False, False)
        hbox.pack_start(gtk.Label('Regex:'), False, False)
        regex_store = gtk.ListStore(str)
        for regex in self.config.regexes:
            regex_store.append([regex])
        regex = gtk.ComboBoxEntry(regex_store)
        regex.child.modify_font(pango.FontDescription("monospace 10"))
        hbox.pack_start(regex)
        extract = gtk.Button('Extract Info')
        hbox.pack_start(extract, False, False)
        def on_extract(*args):
            self.extract_info()
            self.update_previews()
            self.update_info()
        extract.connect('clicked', on_extract)
        self.regex_store, self.regex = regex_store, regex

        # List
        paned = gtk.HPaned()
        vbox.pack_start(paned)

        sw = gtk.ScrolledWindow()
        paned.pack1(sw)
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        self.filelist_model = FileListStore(sys.argv[1:])
        self.filelist_view = FileListView(self.filelist_model)
        self.filelist_view.get_selection().connect('changed', self.update_info)
        sw.add(self.filelist_view)

        sw = gtk.ScrolledWindow()
        paned.pack2(sw, False, False)
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)

        self.info_view = InfoView()
        self.info_view.connect('info-changed', self.update_previews)
        sw.add(self.info_view)

        # Template combo box
        hbox = gtk.HBox(False, 6)
        hbox.pack_start(gtk.Label('Template:'), False, False)
        template_store = gtk.ListStore(str)
        for template in self.config.templates:
            template_store.append([template])
        template = gtk.ComboBoxEntry(template_store)
        template.child.modify_font(pango.FontDescription("monospace 10"))
        template.connect('changed', self.update_previews)
        self.template_store, self.template = template_store, template
        hbox.pack_start(template)
        vbox.pack_start(hbox, False, False)

        # Rename button
        rename = gtk.Button('Rename')
        vbox.pack_start(rename, False, False)

        self.add(vbox)
        self.show_all()

    def run(self):
        gtk.main()

    def quit(self, *args):
        gtk.main_quit()
        self.config.save()

    def get_regex(self):
        iter = self.regex.get_active_iter()
        if iter:
            return self.regex_store.get_value(iter, 0)
        else:
            return self.regex.child.get_text()

    def get_template(self):
        iter = self.template.get_active_iter()
        if iter:
            return self.template_store.get_value(iter, 0)
        else:
            return self.template.child.get_text()

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
        