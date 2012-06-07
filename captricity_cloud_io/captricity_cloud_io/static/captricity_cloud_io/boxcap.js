/* All Backbone models and views related to box communication */

/* Represents a folder on box.com */
var BoxFolder = Backbone.Model.extend({
    initialize: function() {
        this.folders = new BoxFolders(); // Folders in the folder
        this.files = new BoxFiles(); // Files in the folder
        this.populated = false; // If the files and folders have been populated or not
        this.set({selected: false, hidden: true}); // if this folder is selected, hidden
    },

    /*
     * Method to fetch from box the information. Not using "fetch" because response from box
     *   is not in the right format compatible with backbone to auto populate models.
     *   Thus we need a custom method to fetch from the box server.
     */
    populateItems: function() {
        if(!this.populated) {
            var folder = this;
            $.ajax({
                async: false,
                url: base_yql + encodeURIComponent(base_query + "'https://www.box.net/api/1.0/rest?action=get_account_tree&api_key=" + box_api_key + "&auth_token=" + auth_token + "&folder_id=" + this.id + "&params[]=onelevel&params[]=nozip'"),
                dataType: "json",
                success: function(response) {
                    if (response.query.results.response.tree.folder.folders) {
                        folder.folders.populate(response.query.results.response.tree.folder.folders);
                    }
                    if (response.query.results.response.tree.folder.files) {
                        folder.files.populate(response.query.results.response.tree.folder.files.file);
                    }
                }
            });
            this.populated = true;
        }
    },

    // Helper method to select all the items inside the folder
    selectAllFiles: function(selectValue) {
        if(!this.populated) {
            this.populateItems();
        }
        this.folders.each(function (folder) {
            folder.selectAllFiles(selectValue);
        });
        this.files.each(function (file) {
            file.set({selected : selectValue});
        });
    }
});

/* Represents a file on box.com */
var BoxFile = Backbone.Model.extend({
    initialize: function() {
        this.bind("change:selected", this.updateSelectedFiles);
        this.set({selected: false});
    },

    // Add to the collection of selected files when this file is selected
    updateSelectedFiles: function() {
        if (this.get('selected')) {
            window.selectedFiles.add(this);
        }
        else {
            window.selectedFiles.remove(this);
        }
    },
});

/* Represents a collection of box folders */
var BoxFolders = Backbone.Collection.extend({
    model: BoxFolder,

    // Custom method to populate the collection.
    populate: function(rawFolders) {
        var folders = new Array();
        for (var folder in rawFolders) {
            folders.push(rawFolders[folder]);
        }
        this.reset(folders);
    }
});

/* Represents a collection of box files */
var BoxFiles = Backbone.Collection.extend({
    model: BoxFile,

    // Custom method to populate the collection.
    populate: function(rawFiles) {
        this.reset(rawFiles);
    },

    // Sort the collection by name using naturalStringCompare, david koelle's algorithm
    naturalSort: function() {
        this.reset(this.models.sort( function(a, b) {
            return naturalStringCompare(a.get('file_name'), b.get('file_name'));
        }));
    },
});

/* View for one single folder */
var BoxFolderView = Backbone.View.extend({
    tagName: 'li',
    template: _.template($('#folders-template').html()),

    initialize: function() {
        _.bindAll(this, 'render');
        this.model.set({hidden: true});
        this.model.bind('change', this.render);
    },

    events: {
        'click .show': 'showFolder',
        'click .hide': 'hideFolder',
        'click .select-folder': 'selectFolder',
    },

    showFolder: function(e) {
        if ($(e.currentTarget).attr('id') == this.model.get('id')) {
            this.model.populateItems();
            this.model.set({hidden: false});
        }
    },

    hideFolder: function(e) {
        if ($(e.currentTarget).attr('id') == this.model.get('id')) {
            this.model.set({hidden: true});
        }
    },

    selectFolder: function(e) {
        if ($(e.currentTarget).attr('id') == this.model.get('id')) {
            this.model.selectAllFiles($(e.currentTarget).attr('checked') == 'checked');
        }
    },

    /* Render the folder information + buttons and elements to interact with it,
     * then the list of folders inside the folder, and finally the list of files.
     * Only show it if the folder is not marked to hide elements and if the folder has
     * stuff inside it. 
     */
    render: function() {
        $(this.el).html(this.template(this.model.toJSON()));

        if ((this.model.folders.length > 0 || this.model.files.length > 0) && !this.model.get('hidden')) {
            var subFolderListView = new BoxListView({});
            subFolderListView.folders = this.model.folders;
            subFolderListView.files = this.model.files;
            $(this.el).append(subFolderListView.render().el);
        }
        return this;
    }
});

/* View for one single file */
var BoxFileView = Backbone.View.extend({
    tagName: 'li',
    template: _.template($('#file-template').html()),

    initialize: function() {
        _.bindAll(this, 'render');
        this.model.bind('change', this.render);
    },

    events: {
        'click .select-file' : 'toggleSelect'
    },

    toggleSelect: function(e) {
        if ($(e.currentTarget).attr('id') == this.model.get('id')) {
            this.model.set({ selected : $(e.currentTarget).attr('checked') == 'checked' });
        }
    },

    render: function() {
        $(this.el).html(this.template(this.model.toJSON()));
        return this;
    }
});

/* View for the list of files and folders */
var BoxListView = Backbone.View.extend({
    tagName: 'div',
    className: 'folder-tree',
    template: _.template($('#folder-tree-template').html()),

    /* List the folders first, then the files */
    render: function() {
        $(this.el).html(this.template({}));
        var $items = this.$('.folders-list');
        this.folders.each(function (folder) {
            var view = new BoxFolderView({
                model: folder,
            });
            $items.append(view.render().el);
        });
        this.files.each(function (file) {
            var view = new BoxFileView({
                model: file,
            });
            $items.append(view.render().el);
        });
        return this;
    }
});

/* View for the list of files that have been selected */
var SelectedQueueView = Backbone.View.extend({
    tagName: 'div',
    className: 'selected-queue',
    template: _.template($('#selected-queue-template').html()),
    listElName: '.selected-files-list',

    initialize: function() {
        _.bindAll(this, 'render');
        window.selectedFiles.bind('add', this.render);
        window.selectedFiles.bind('remove', this.render);
    },

    events: {
        'click .upload' : 'uploadFiles'
    },

    /* Upload the list of files to cap by hitting the view that will queue a celery task to
     * download the specified files from box.com
     */
    uploadFiles: function() {
        // post to upload view
        window.selectedFiles.naturalSort();
        alert("Will upload: " + window.selectedFiles.pluck('file_name'));
        $.ajax({
            type: 'POST',
            url: '/boxcap/upload/',
            dataType: 'json',
            data: {
                auth_token: window.auth_token,
                ticket: window.ticket,
                job_id: window.selectedJob.get('id'),
                files: JSON.stringify(window.selectedFiles.map(function(file) {
                    return {
                        url: "https://www.box.net/api/1.0/download/" + window.auth_token + "/" + file.get('id'),
                        name: file.get('file_name'),
                    };
                })),
            },
            success: function(response) {
                if (response.status == 'success') {
                    alert("Successfully initiated download task on Captricity");
                    window.App.navigate('', true);
                }
                else {
                    alert("Unsuccessful initiation of download task");
                }
            },
        });
    },

    /* Simply list out each file that is selected */
    render: function() {
        $(this.el).html(this.template({}));
        var $files = this.$(this.listElName);
        window.selectedFiles.each(function (file) {
            var view = new SelectedFileView({
                model: file
            });
            $files.append(view.render().el);
        });
        return this;
    }
});

/* Just show the file name */
var SelectedFileView = Backbone.View.extend({
    tagName: 'li',
    className: 'selected-file',

    render: function() {
        $(this.el).html(this.model.get('file_name'));
        return this;
    }
});

