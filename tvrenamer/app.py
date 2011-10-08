
import sys
import gtk
import os
import shutil


class TVRenamer(gtk.Window):

    (FILENAME_COL,
     EPISODE_COL,
     TITLE_COL,
     BASENAME_COL) = range(4)

    def __init__(self):
        super(TVRenamer, self).__init__()
        
        self.connect("destroy", gtk.main_quit)
        self.set_size_request(800, 600)
        self.set_position(gtk.WIN_POS_CENTER)

        vbox = gtk.VBox(False, 12)
        vbox.set_border_width(12)

        hbox = gtk.HBox(False, 6)
        hbox.pack_start(gtk.Label('Regex:'), False, False)
        regex = gtk.ComboBoxEntry()
        hbox.pack_start(regex)

        vbox.pack_start(hbox, False, False)
        
        sw = gtk.ScrolledWindow()
        sw.set_shadow_type(gtk.SHADOW_ETCHED_IN)
        sw.set_policy(gtk.POLICY_AUTOMATIC, gtk.POLICY_AUTOMATIC)
        
        vbox.pack_start(sw, True, True, 0)

        self.store = self.create_model()
        self.store.set_sort_column_id(self.EPISODE_COL, gtk.SORT_ASCENDING)

        self.tree_view = gtk.TreeView(self.store)
        # tree_view.connect("row-activated", self.on_activated)
        self.tree_view.set_rules_hint(True)
        self.tree_view.set_reorderable(True)
        self.tree_view.set_headers_clickable(True)
        self.tree_view.get_selection().set_mode(gtk.SELECTION_MULTIPLE)
        self.tree_view.add_events(gtk.gdk.KEY_PRESS_MASK)
        self.tree_view.connect('key-press-event', self.on_treeview_keypress)
        sw.add(self.tree_view)

        self.create_columns()

        hbox = gtk.HBox(False, 6)
        season = gtk.Entry()
        hbox.pack_start(season, False, False)
        series = gtk.Entry()
        hbox.pack_start(series)
        vbox.pack_start(hbox, False, False)
        
        rename = gtk.Button('Rename')
        vbox.pack_start(rename, False, False)

        self.add(vbox)
        self.show_all()


    def create_model(self):
        store = gtk.ListStore(str, int, str, str)

        for filename in sys.argv[1:]:
            store.append([
                filename,
                0,
                '',
                os.path.splitext(os.path.basename(filename))[0]
            ])

        return store


    def create_columns(self):
        cell = gtk.CellRendererText()
        cell.set_property('editable', True)
        cell.connect('edited', self.on_cell_edited, self.EPISODE_COL)
        column = gtk.TreeViewColumn("Episode", cell, text=self.EPISODE_COL)
        column.set_sort_column_id(self.EPISODE_COL)
        self.tree_view.append_column(column)

        cell = gtk.CellRendererText()
        cell.set_property('editable', True)
        cell.connect('edited', self.on_cell_edited, self.TITLE_COL)
        column = gtk.TreeViewColumn("Title", cell, text=self.TITLE_COL)
        self.tree_view.append_column(column)

        cell = gtk.CellRendererText()
        cell.set_property('editable', True)
        column = gtk.TreeViewColumn("Filename", cell, text=self.BASENAME_COL)
        column.set_sort_column_id(self.BASENAME_COL)
        self.tree_view.append_column(column)
        
    def on_cell_edited(self, cell, path, new_text, column):
        if column == self.EPISODE_COL:
            episode = int(new_text)
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


TVRenamer()
gtk.main()
