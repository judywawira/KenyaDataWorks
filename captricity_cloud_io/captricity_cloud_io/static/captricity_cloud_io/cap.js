var Sheet = Backbone.Model.extend({});

var Job = Backbone.Model.extend({
    initialize: function() {
        this.set({selected: false});
    }
});
var JobCollection = Backbone.Collection.extend({
    model: Job,
    url: '/cap-jobs/'
});

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
        window.jobs.bind('reset', this.render);
    },

    events: {
        'click .select': 'selectJob',
    },

    selectJob: function() {
        window.App.navigate('next', true);
    },

    render: function() {
        $(this.el).html(this.template({}));
        var $jobs = this.$('.job-list');
        window.jobs.each(function (job) {
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
        _.each(window.selectedJob.get('document')['sheets'], function(sheet) {
            var view = new SheetImageView({
                model: new Sheet(sheet)
            });
            $sheets.append(view.render().el);
        });
        return this;
    }
});
