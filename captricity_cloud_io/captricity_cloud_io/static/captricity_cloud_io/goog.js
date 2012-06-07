var Spreadsheet = Backbone.Model.extend({
    initialize: function() {
        this.set({selected: false});
    }
});
var SpreadsheetCollection = Backbone.Collection.extend({
    model: Spreadsheet,
    url: '/gdata-resources/'
});

var SpreadsheetView = Backbone.View.extend({
    tagName: 'li',
    template: _.template($('#gdata-spreadsheet-template').html()),

    initialize: function() {
        _.bindAll(this, 'render');
        this.model.bind('change', this.render);
    },

    events: {
        'click .select-spreadsheet' : 'toggleSelect'
    },

    toggleSelect: function(e) {
        if ($(e.currentTarget).attr('id') == this.model.get('id')) {
            window.selectedSpreadsheet = this.model;
            this.model.set({ selected : $(e.currentTarget).attr('checked') == 'checked' });
        }
    },

    render: function() {
        $(this.el).html(this.template(this.model.toJSON()));
        return this;
    }
});

var SpreadsheetListView = Backbone.View.extend({
    tagName: 'div',
    className: 'spreadsheet-list-view',
    template: _.template($('#gdata-spreadsheet-list-template').html()),

    initialize: function() {
        _.bindAll(this, 'render');
    },

    events: {
        'click .sync': 'syncJobSpreadsheet',
        'click .new-sync': 'syncJobCreateSpreadsheet',
    },

    syncJobSpreadsheet: function() {
        $.ajax({
            type: 'POST',
            url: '/register-sync/',
            dataType: 'json',
            data: { 
                document_name: window.selectedJob.get('document')['name'],
                spreadsheet_id: window.selectedSpreadsheet.get('id'),
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

    syncJobCreateSpreadsheet: function() {
        $.ajax({
            type: 'POST',
            url: '/register-create-sync/',
            dataType: 'json',
            data: { 
                job_id: window.selectedJob.get('id'),
            },
            success: function(response) {
                if (response.status == 'success') {
                    alert("Successfully initiated download task on Captricity");
                }
                else {
                    alert("Unsuccessful initiation of download task");
                }
            },
        });
    },

    render: function() {
        $(this.el).html(this.template({}));
        var $spreadsheets = this.$('.spreadsheet-list');
        window.spreadsheets.each(function (spreadsheet) {
            if (spreadsheet != undefined) {
                var view = new SpreadsheetView({
                    model: spreadsheet,
                });
                $spreadsheets.append(view.render().el);
            }
        });
        return this;
    }
});
