// Obtained from nutria: https://github.com/Captricity/nutria

var captricity = captricity || {};

captricity.APIResource = Backbone.Model.extend({});

captricity.APISchema = Backbone.Collection.extend({
    model: captricity.APIResource,
    url: '{{ CAPTRICITY_SCHEMA_URL }}',
});

captricity.APISchema.prototype.initialize = function(){
    this.bind('reset', this.generateBackboneClasses, this);
}

captricity.APISchema.prototype.parse = function(response){
    this.name = response.name;
    this.endpoint = response.endpoint;
    this.version = response.version;
    return response.resources;
}

captricity.APISchema.prototype.generateBackboneClasses = function(){
    //This empties out captricity.api and populates it with Backbone Models and Collections for each resource in the schema.
    captricity.api = {};

    // First set up the non-list resources as Models
    for(var i=0; i < this.models.length; i++){
        if(this.models[i].get('is_list')) continue;
        var resourceModel = this.models[i];
        var modelName = this.resourceNameToModelName(resourceModel.get('name'));
        var initial_data = {
            regex: resourceModel.get('regex'),
            doc: resourceModel.get('doc'),
            supported: resourceModel.get('supported'),
            arguments: resourceModel.get('arguments'),
            schema: this,
        };
        captricity.api[modelName] = captricity.APIModel.extend(initial_data);
    }

    // Not set up the list resources as Collections
    for(var i=0; i < this.models.length; i++){
        if(!this.models[i].get('is_list')) continue;
        var resourceModel = this.models[i];
        var modelName = this.resourceNameToModelName(resourceModel.get('name'));
        var initial_data = {
            regex: resourceModel.get('regex'),
            doc: resourceModel.get('doc'),
            supported: resourceModel.get('supported'),
            arguments: resourceModel.get('arguments'),
            schema: this,
        };
        // Check to see if we can use one of the previously defined resource Models as this collection's model
        if(resourceModel.get('listed_resource')){
            var childModelName = this.resourceNameToModelName(resourceModel.get('listed_resource'));
            initial_data['model'] = captricity.api[childModelName];
        }
        captricity.api[modelName] = captricity.APICollection.extend(initial_data);
    }
}

captricity.APISchema.prototype.resourceNameToModelName = function(resourceName){
    // Convert a resource name like box_model to BoxModel
    var tokens = resourceName.split('_');
    for(var i=0; i < tokens.length; i++){
        tokens[i] = tokens[i].charAt(0).toUpperCase() + tokens[i].substring(1,tokens[i].length);
    }
    return tokens.join('');
}

captricity.APICollection = Backbone.Collection.extend({});

captricity.APICollection.prototype.url = function(){
    return captricity.generateSchemaURL(this);
}

captricity.APIModel = Backbone.Model.extend({});

captricity.APIModel.prototype.url = function(){
    return captricity.generateSchemaURL(this);
}

captricity.apiSync = function(method, model, options){
    var version = this.__proto__.schema.version;
    var new_options =  _.extend({
        beforeSend: function(xhr) {
            xhr.setRequestHeader('X_API_TOKEN', window.captricityApiToken);
            xhr.setRequestHeader('X_API_VERSION', version);
        }
    }, options)
    Backbone.sync(method, model, new_options);
}

captricity.APICollection.prototype.sync = captricity.apiSync;
captricity.APIModel.prototype.sync = captricity.apiSync;

captricity.generateSchemaURL = function(instance){
    regexTokens = captricity.splitSchemaRegex(instance.__proto__.regex);
    result = ''
    for(var i=0; i < instance.__proto__.arguments.length; i++){
        result = result + regexTokens[i] + instance[instance.__proto__.arguments[i]];
    }
    if(regexTokens.length > instance.__proto__.arguments.length){
        result = result + regexTokens[regexTokens.length - 1]
    }
    var hostURL = captricity.getHostURL('{{CAPTRICITY_SCHEMA_URL}}');
    return hostURL + result
}

captricity.getHostURL = function(url){
    var a = document.createElement('a');
    a.href = url;
    if(a.port != '80' && a.port != '') return a.protocol + '//' + a.hostname + ':' + a.port;
    return a.protocol + '//' + a.hostname;
}

captricity.splitSchemaRegex = function(regex){
    // Return an array of the URL split at each regex match like (?P<id>[\d]+)
    ///Call with a regex of '^/foo/(?P<id>[\d]+)/bar/$' and you will receive ['/foo/', '/bar/']
    if(regex.charAt(0) == '^') regex = regex.substring(1, regex.length);
    if(regex.charAt(regex.length - 1) == '$') regex = regex.substring(0, regex.length - 1)
    results = []
    line = ''
    for(var i =0; i < regex.length; i++){
    	var c = regex.charAt(i);
        if(c == '('){
            results[results.length] = line;
            line = '';
        } else if(c == ')'){
            line = '';
        } else {
            line = line + c;
        }
    }
    if(line.length > 0) results[results.length] = line
    return results
}

captricity.parseJSONDate = function(jsonDate){
    //takes a jsonDate as provided by backbone: "2012-04-24 13.55.03" and returns a Javascript Date instance
    var dateString = jsonDate.split('T')[0];
    var timeArray = jsonDate.split('T')[1].split(':');
    var date = $.datepicker.parseDate('yy-mm-dd', dateString);
    return new Date(date.getFullYear(), date.getMonth(), date.getDate(), parseInt(timeArray[0], 10), parseInt(timeArray[1], 10), parseInt(timeArray[2], 10));
}
