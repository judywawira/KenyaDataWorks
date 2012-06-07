var CmisFolder = Backbone.Model.extend({
    urlRoot: '/cmis-folder/',

    initialize: function() {
        this.folders = new CmisFolders();
        this.files = new CmisFiles();
        this.set({selected: false, hidden: true});
    },

    parse: function(resp, xhr) {
        this.folders.reset(resp['subfolders'])
        this.files.reset(resp['files'])
        delete resp['subfolders']
        delete resp['files']
        return resp;
    },

    // Helper method to select all the items inside the folder
    selectAllFiles: function(selectValue) {
        this.folders.each(function (folder) {
            folder.selectAllFiles(selectValue);
        });
        this.files.each(function (file) {
            file.set({selected : selectValue});
        });
    }
});

var CmisFile = Backbone.Model.extend({
    urlRoot: '/cmis-file/',

    initialize: function() {
        this.bind("change:selected", this.updateSelectedFiles);
        this.set({selected:false});
    },

    updateSelectedFiles: function() {
        if (this.get('selected')) {
            window.selectedFiles.add(this);
        }
        else {
            window.selectedFiles.remove(this);
        }
    },
});

var CmisFolders = Backbone.Collection.extend({
    model: CmisFolder,
});

var CmisFiles = Backbone.Collection.extend({
    model: CmisFile,

    // Sort the collection by name using naturalStringCompare, david koelle's algorithm
    naturalSort: function() {
        this.reset(this.models.sort( function(a, b) {
            return naturalStringCompare(a.get('name'), b.get('name'));
        }));
    },

});

var CmisFolderView = Backbone.View.extend({
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
            this.model.fetch();
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

    render: function() {
        $(this.el).html(this.template(this.model.toJSON()));

        if ((this.model.folders.length > 0 || this.model.files.length > 0) && !this.model.get('hidden')) {
            var subFolderListView = new CmisListView({});
            subFolderListView.folders = this.model.folders;
            subFolderListView.files = this.model.files;
            $(this.el).append(subFolderListView.render().el);
        }
        return this;
    }
});

/* View for one single file */
var CmisFileView = Backbone.View.extend({
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
var CmisListView = Backbone.View.extend({
    tagName: 'div',
    className: 'folder-tree',
    template: _.template($('#folder-tree-template').html()),

    /* List the folders first, then the files */
    render: function() {
        $(this.el).html(this.template({}));
        var $items = this.$('.folders-list');
        this.folders.each(function (folder) {
            var view = new CmisFolderView({
                model: folder,
            });
            $items.append(view.render().el);
        });
        this.files.each(function (file) {
            var view = new CmisFileView({
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
        alert("Will upload: " + window.selectedFiles.pluck('name'));
        $.ajax({
            type: 'POST',
            url: '/upload_cmis_to_captricity/',
            dataType: 'json',
            data: {
                job_id: window.selectedJob.get('id'),
                file_ids: JSON.stringify(window.selectedFiles.pluck('id')),
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
        $(this.el).html(this.model.get('name'));
        return this;
    }
});



