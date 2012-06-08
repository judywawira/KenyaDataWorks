var JobView = Backbone.View.extend({
    tagName: 'li',
    template: _.template($('#job-template').html()),

    events: {
        'click .select-job' : 'toggleSelect'
    },

    toggleSelect: function(e) {
        if ($(e.currentTarget).attr('id') == this.model.get('id')) {
            window.selectedJob = this.model;
            this.model.set({ selected : $(e.currentTarget).attr('checked') == 'checked' });
        }
    },

    initialize: function() {
        _.bindAll(this, 'render');
        if (this.model.get('selected') == undefined) {
            this.model.set({ selected: false });
        }
    },

    render: function() {
        $(this.el).html(this.template(this.model.toJSON()));
        return this;
    }
});

var JobListView = Backbone.View.extend({
    tagName: 'div',
    className: 'job-list-view',
    template: _.template($('#job-selection-list-template').html()),

    initialize: function() {
        _.bindAll(this, 'render');
        this.failedFetch = false;
        this.collection = new captricity.api.Jobs();
        this.collection.bind('reset', this.render, this);
        this.collection.fetch({
            success: this.handleFetchSuccess,
            error: this.handleFetchError,
            data: $.param({ status: 'setup' }),
        });
    },

    handleFetchSuccess: function(collection, response){
        this.failedFetch = false;
    },

    handleFetchError: function(collection, response){
        console.log(response);
        this.failedFetch = true;
        this.render();
    },

    events: {
        'click .select': 'selectJob',
    },

    selectJob: function() {
        window.App.navigate('next', true);
    },

    render: function() {
        if(this.failedFetch){
            $(this.el).append('<h2>Failed to fetch your list of jobs.</h2>');
            $(this.el).append('<p>Is the API token set on your user profile?</p>');
            return this;
        }
        if(this.collection.length == 0){
            $(this.el).append('<h2>No jobs found.</h2>');
            return this;
        }
        
        $(this.el).html(this.template({}));
        var $jobs = this.$('.job-list');
        this.collection.each(function (job) {
            var view = new JobView({
                model: job
            });
            $jobs.append(view.render().el);
        });
        return this;
    }
});

var SheetImageView = Backbone.View.extend({
    tagName: 'li',
    className: 'job-sheet-image-view',
    template: _.template($('#job-sheet-image-template').html()),

    initialize: function() {
        _.bindAll(this, 'render');
    },

    render: function() {
        $(this.el).html(this.template(this.model.toJSON()));
        return this;
    }
});

var DocumentListView = Backbone.View.extend({
    tagName: 'div',
    className: 'job-document-view',
    template: _.template($('#job-document-template').html()),

    initialize: function() {
        _.bindAll(this, 'render');
        this.document = window.selectedJob.get('document');
    },

    handleFetchSuccess: function(collection, response){
        this.failedFetch = false;
    },

    handleFetchError: function(collection, response){
        this.failedFetch = true;
        this.render();
    },

    events: {
        'click .continue': 'continueSelection',
        'click .abort': 'abortSelection',
    },

    continueSelection: function() {
        window.App.navigate('sync', true);
    },

    abortSelection: function() {
        window.App.navigate('', true);
    },

    render: function() {
        $(this.el).html(this.template({}));
        var $sheets = this.$('.sheet-list');
        _.each(this.document['sheets'], function(sheet) {
            var sheet_model = new captricity.api.Sheet(id=sheet['id'])
            sheet_model.fetch({
                success: this.handleFetchSuccess,
                error: this.handleFetchError
            });
            var view = new SheetImageView({
                model: sheet_model,
            });
            $sheets.append(view.render().el);
        });
        return this;
    }
});
