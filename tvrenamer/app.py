
import sys
import gtk
import pango
import os
import re
import shutil

from jinja2 import Template
from jinja2.exceptions import TemplateSyntaxError

from .config import Config


class TVRenamer(gtk.Window):

    (FILENAME_COL,
     EPISODE_COL,
     TITLE_COL,
     BASENAME_COL,
     PREVIEW_COL) = range(5)

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
        hbox.pack_start(gtk.Label('Regex:'), False, False)
        self.regex_store = gtk.ListStore(str)
        for regex in self.config.regexes:
            self.regex_store.append([regex])
        regex = gtk.ComboBoxEntry(self.regex_store)
        regex.child.modify_font(pango.FontDescription("monospace 10"))
        regex.connect('changed', self.parse)
        self.regex = regex
        hbox.pack_start(regex)
        vbox.pack_start(hbox, False, False)

        # Format combo box
        hbox = gtk.HBox(False, 6)
        hbox.pack_start(gtk.Label('Format:'), False, False)
        format_store = gtk.ListStore(str)
        for format in self.config.formats:
            format_store.append([format])
        format = gtk.ComboBoxEntry(format_store)
        format.child.modify_font(pango.FontDescription("monospace 10"))
        format.connect('changed', self.parse)
        self.format_store, self.format = format_store, format
        hbox.pack_start(format)
        vbox.pack_start(hbox, False, False)

        # List
        sw = gtk.ScrolledWindow()
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        vbox.pack_start(sw, True, True, 0)

        self.store = self.create_model()
        self.store.set_sort_column_id(self.EPISODE_COL, gtk.SORT_ASCENDING)

        self.tree_view = gtk.TreeView(self.store)
        self.tree_view.set_rules_hint(True)
        self.tree_view.set_reorderable(True)
        self.tree_view.set_headers_clickable(True)
        self.tree_view.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        self.tree_view.add_events(gtk.gdk.KEY_PRESS_MASK)
        self.tree_view.connect('key-press-event', self.on_treeview_keypress)
        sw.add(self.tree_view)

        self.create_columns()

        # Season input
        hbox2 = gtk.HBox(False, 24)
        hbox = gtk.HBox(False, 6)
        hbox.pack_start(gtk.Label('Season:'), False, False)
        season = gtk.SpinButton()
        season.set_range(0, 999)
        season.set_numeric(True)
        season.set_increments(1, 5)
        hbox.pack_start(season, False, False)
        hbox2.pack_start(hbox, False, False)

        # Show title input
        hbox = gtk.HBox(False, 6)
        hbox.pack_start(gtk.Label('Show Title:'), False, False)
        series = gtk.Entry()
        hbox.pack_start(series)
        hbox2.pack_start(hbox)
        vbox.pack_start(hbox2, False, False)

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

    def parse(self, *args):
        iter = self.regex.get_active_iter()
        if iter:
            regex = self.regex_store.get_value(iter, 0)
        else:
            regex = self.regex.child.get_text()
        print regex
        regex = re.compile(regex)
        show_data = {
            'show': '',
            'year': '2011',
            'season': 5,
        }
        for row in self.store:
            data = show_data.copy()
            data['episode'] = row[self.EPISODE_COL]
            data['title'] = row[self.TITLE_COL]
            basename = row[self.BASENAME_COL]
            match = regex.match(basename)
            if not match:
                row[self.PREVIEW_COL] = ''
                continue
            data.update(match.groupdict())
            preview = self.format_new_path(data)
            if preview is not None:
                row[self.PREVIEW_COL] = preview

    def format_new_path(self, data):
        iter = self.format.get_active_iter()
        if iter:
            format = self.format_store.get_value(iter, 0)
        else:
            format = self.format.child.get_text()
        try:
            template = Template(format)
            return template.render(data)
        except TemplateSyntaxError:
            return

    def create_model(self):
        store = gtk.ListStore(str, int, str, str, str)

        for filename in sys.argv[1:]:
            store.append([
                filename,
                0,
                '',
                os.path.splitext(os.path.basename(filename))[0],
                ''
            ])

        return store


    def create_columns(self):
        cell = gtk.CellRendererSpin()
        cell.set_property('editable', True)
        adjustment = gtk.Adjustment(0, 0, 999, 1, 5)
        cell.set_property('adjustment', adjustment)
        cell.connect('edited', self.on_cell_edited, self.EPISODE_COL)
        column = gtk.TreeViewColumn("Episode", cell, text=self.EPISODE_COL)
        column.set_sort_column_id(self.EPISODE_COL)
        self.tree_view.append_column(column)

        cell = gtk.CellRendererText()
        cell.set_property('editable', True)
        cell.connect('edited', self.on_cell_edited, self.TITLE_COL)
        column = gtk.TreeViewColumn("Title", cell, text=self.TITLE_COL)
        column.set_resizable(True)
        self.tree_view.append_column(column)

        cell = gtk.CellRendererText()
        cell.set_property('editable', True)
        column = gtk.TreeViewColumn("Filename", cell, text=self.BASENAME_COL)
        column.set_sort_column_id(self.BASENAME_COL)
        column.set_resizable(True)
        self.tree_view.append_column(column)

        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn("Preview", cell, text=self.PREVIEW_COL)
        column.set_resizable(True)
        self.tree_view.append_column(column)

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

    def on_treeview_keypress(self, widget, event):
        keyname = gtk.gdk.keyval_name(event.keyval)
        if keyname == 'Delete':
            selection = self.tree_view.get_selection()
            model, selected = selection.get_selected_rows()
            iters = [model.get_iter(path) for path in selected]
            next_iter = model.iter_next(iters[-1]) if len(iters) else None
            for iter in iters:
                model.remove(iter)
            if next_iter:
                selection.select_iter(next_iter)

    def on_configure_event(self, widget, event):
        self.config.width, self.config.height = event.width, event.height
