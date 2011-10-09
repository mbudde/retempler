
import os
import gtk
import re

from jinja2 import Template
from jinja2.exceptions import TemplateSyntaxError


class FileListStore(gtk.ListStore):

    (COLUMN_FILENAME,
     COLUMN_BASENAME,
     COLUMN_PREVIEW,
     COLUMN_FILEINFO) = range(4)

    def __init__(self, filenames):
        super(FileListStore, self).__init__(str, str, str, object)
        self.set_sort_column_id(self.COLUMN_BASENAME, gtk.SORT_ASCENDING)

        for filename in filenames:
            self.append([
                filename,
                os.path.splitext(os.path.basename(filename))[0],
                None,
                None
            ])

    def extract_info(self, iter, regex):
        basename = self.get_value(iter, self.COLUMN_BASENAME)
        match = re.match(regex, basename)
        if match:
            info = self.get_value(iter, self.COLUMN_FILEINFO)
            if info is None:
                info = {}
            info.update(match.groupdict())
            self.set_value(iter, self.COLUMN_FILEINFO, info)

    def extract_info_all(self, regex):
        iter = self.get_iter_first()
        while iter:
            self.extract_info(iter, regex)
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

    def render_preview_all(self, template):
        try:
            template = Template(template)
        except TemplateSyntaxError:
            return
        iter = self.get_iter_first()
        while iter:
            self.render_preview(iter, template)
            iter = self.iter_next(iter)


class FileListView(gtk.TreeView):

    def __init__(self, model=None):
        super(FileListView, self).__init__(model)
        self.set_rules_hint(True)
        self.set_reorderable(True)
        self.set_headers_clickable(True)
        self.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        self.add_events(gtk.gdk.KEY_PRESS_MASK)
        self.connect('key-press-event', self.on_keypress)

        # cell = gtk.CellRendererSpin()
        # cell.set_property('editable', True)
        # adjustment = gtk.Adjustment(0, 0, 999, 1, 5)
        # cell.set_property('adjustment', adjustment)
        # cell.connect('edited', self.on_cell_edited, self.EPISODE_COL)
        # column = gtk.TreeViewColumn('Episode', cell, text=self.EPISODE_COL)
        # column.set_sort_column_id(self.EPISODE_COL)
        # self.append_column(column)

        # cell = gtk.CellRendererText()
        # cell.set_property('editable', True)
        # cell.connect('edited', self.on_cell_edited, self.TITLE_COL)
        # column = gtk.TreeViewColumn('Title', cell, text=self.TITLE_COL)
        # column.set_resizable(True)
        # self.append_column(column)

        cell = gtk.CellRendererText()
        # cell.set_property('editable', True)
        column = gtk.TreeViewColumn('Filename', cell, text=FileListStore.COLUMN_BASENAME)
        column.set_sort_column_id(FileListStore.COLUMN_BASENAME)
        column.set_resizable(True)
        self.append_column(column)

        cell = gtk.CellRendererText()
        column = gtk.TreeViewColumn('Preview', cell, text=FileListStore.COLUMN_PREVIEW)
        column.set_resizable(True)
        self.append_column(column)

    def on_keypress(self, widget, event):
        keyname = gtk.gdk.keyval_name(event.keyval)
        if keyname == 'Delete':
            selection = self.get_selection()
            model, selected = selection.get_selected_rows()
            iters = [model.get_iter(path) for path in selected]
            next_iter = model.iter_next(iters[-1]) if len(iters) else None
            for iter in iters:
                model.remove(iter)
            if next_iter:
                selection.select_iter(next_iter)
