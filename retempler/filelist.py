
import os
import re

from gi.repository import Gtk, Gdk, GObject

from jinja2 import Template
from jinja2.exceptions import TemplateSyntaxError


class FileListStore(Gtk.ListStore):

    (COLUMN_FILENAME,
     COLUMN_BASENAME,
     COLUMN_PREVIEW,
     COLUMN_FILEINFO,
     COLUMN_RENAMED) = range(5)

    def __init__(self):
        super(FileListStore, self).__init__(str, str, str, object, str)
        self.set_sort_column_id(self.COLUMN_BASENAME, Gtk.SortType.ASCENDING)

    def add_paths(self, paths):
        for path in paths:
            if os.path.isdir(path):
                for root, dirs, files in os.walk(path):
                    for name in files:
                        self.add_file(os.path.join(root, name))
            elif os.path.isfile(path):
                self.add_file(path)

    def add_file(self, filename):
        self.append([
            filename,
            os.path.splitext(os.path.basename(filename))[0],
            None,
            {},
            Gtk.STOCK_NO,
        ])

    def extract_info(self, iter, regex, match_full_path=False):
        if match_full_path:
            string = self.get_value(iter, self.COLUMN_FILENAME)
        else:
            string = self.get_value(iter, self.COLUMN_BASENAME)
        match = re.match(regex, string)
        if match:
            info = self.get_value(iter, self.COLUMN_FILEINFO)
            info.update(match.groupdict())
            self.set_value(iter, self.COLUMN_FILEINFO, info)

    def extract_info_all(self, *args, **kwargs):
        iter = self.get_iter_first()
        while iter:
            self.extract_info(iter, *args, **kwargs)
            iter = self.iter_next(iter)

    def render_preview(self, iter, template):
        info = self.get_value(iter, self.COLUMN_FILEINFO)
        try:
            if not isinstance(template, Template):
                template = Template(template)
            preview = template.render(info)
            self.set_value(iter, self.COLUMN_PREVIEW, preview)
        except TemplateSyntaxError:
            pass

    def render_preview_all(self, template, *args, **kwargs):
        try:
            template = Template(template)
        except TemplateSyntaxError:
            return
        iter = self.get_iter_first()
        while iter:
            self.render_preview(iter, template, *args, **kwargs)
            iter = self.iter_next(iter)

    def get_destination(self, iter, destination_folder):
        filename = self.get_value(iter, self.COLUMN_FILENAME)
        new_base = self.get_value(iter, self.COLUMN_PREVIEW)
        base, ext = os.path.splitext(filename)
        if new_base:
            new_base = new_base.strip('/')
            return os.path.join(destination_folder, new_base) + ext

    def rename(self, destination_folder):
        iter = self.get_iter_first()
        while iter:
            filename = self.get_value(iter, self.COLUMN_FILENAME)
            dest = self.get_destination(iter, destination_folder)
            try:
                os.renames(filename, dest)
            except OSError:
                self.set_value(iter, self.COLUMN_RENAMED, Gtk.STOCK_STOP)
            else:
                print 'mv "{0}" "{1}"'.format(filename, dest)
                self.set_value(iter, self.COLUMN_RENAMED, Gtk.STOCK_YES)
            iter = self.iter_next(iter)


class FileListView(Gtk.TreeView):

    show_full_path = GObject.property(type=bool, default=False)

    def __init__(self, model=None):
        super(FileListView, self).__init__(model=model)
        self.set_rules_hint(True)
        self.set_headers_clickable(True)
        self.get_selection().set_mode(Gtk.SelectionMode.MULTIPLE)
        self.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        self.connect('key-press-event', self.on_keypress)

        cell = Gtk.CellRendererPixbuf()
        cell.set_property('xpad', 3)
        column = Gtk.TreeViewColumn('', cell, stock_id=FileListStore.COLUMN_RENAMED)
        column.set_resizable(False)
        self.append_column(column)

        filename_cell = Gtk.CellRendererText()
        filename_column = Gtk.TreeViewColumn('Filename', filename_cell,
                                             text=FileListStore.COLUMN_BASENAME)
        filename_column.set_sort_column_id(FileListStore.COLUMN_BASENAME)
        filename_column.set_resizable(True)
        self.append_column(filename_column)

        def update_filename_column(self, prop):
            filename_column.clear_attributes(filename_cell)
            if self.show_full_path:
                column = FileListStore.COLUMN_FILENAME
            else:
                column = FileListStore.COLUMN_BASENAME
            filename_column.add_attribute(filename_cell, 'text', column)
            filename_column.set_sort_column_id(column)
        self.connect('notify::show-full-path', update_filename_column)

        cell = Gtk.CellRendererText()
        column = Gtk.TreeViewColumn('Preview', cell, text=FileListStore.COLUMN_PREVIEW)
        column.set_sort_column_id(FileListStore.COLUMN_PREVIEW)
        column.set_resizable(True)
        self.append_column(column)

    def on_keypress(self, widget, event):
        keyname = Gdk.keyval_name(event.keyval)
        if keyname == 'Delete':
            selection = self.get_selection()
            model, selected = selection.get_selected_rows()
            iters = [model.get_iter(path) for path in selected]
            next_iter = model.iter_next(iters[-1]) if len(iters) else None
            for iter in iters:
                model.remove(iter)
            if next_iter:
                selection.select_iter(next_iter)
