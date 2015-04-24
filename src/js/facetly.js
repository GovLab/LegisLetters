/*! Facetly - v0.1.0 - 2013-11-20
* https://github.com/jiabin/facetly
* Copyright (c) 2013 Eymen Gunay; Licensed MIT */

var Facetly = Facetly || (function($) {

    var Utils     = {}, // Toolbox
        Ajax      = {}, // Ajax Wrapper
        Events    = {}, // Event-based Actions
        Templates = {}, // Handlebar Templates
        UI        = {}, // App Interface
        Lang      = {}, // i18n Support
        Query     = {}, // Elasticsearch Query Helper
        App       = {}, // Global Logic and Initializer
        Public    = {}; // Public Functions

    /* -----------------------------------------
       UTILS
    ----------------------------------------- */
    Utils = {
        settings: {
            debug: true,
            selector: '#facetly',
            elasticsearch: '/elasticsearch/legisletters/letter',
            perPage: 25,
            currentPage: 1,
            excludedFields: [],
            facets: {},
            meta: {},
            onSerialize: function(str, obj) {},
            init: function(settings) {
                _log('Initializing Settings');
                $('meta[name^="facetly-"]').each(function(){
                    Utils.settings.meta[ this.name.replace('facetly-','') ] = this.content;
                });
                Utils.settings = Utils.extend(Utils.settings, settings);
                element = $(Utils.settings.selector);
                _log('Initialized Settings');
            }
        },
        cache: {
            window: window,
            document: document
        },
        extend: function(obj1, obj2) {
            return $.extend(obj1, obj2);
        },
        merge: function(arr1, arr2) {
            return $.merge(arr1, arr2);
        },
        elastic_url: function() {
            return Utils.settings.elasticsearch;
        },
        elastic_search_url: function() {
            return Utils.elastic_url();
        },
        log: function(what) {
            if (Utils.settings.debug) {
                console.log(what);
            }
        },
        parseRoute: function(input) {

            var delimiter = input.delimiter || '/',
                paths = input.path.split(delimiter),
                check = input.target[paths.shift()],
                exists = typeof check != 'undefined',
                isLast = paths.length == 0;
            input.inits = input.inits || [];

            if (exists) {
                if(typeof check.init == 'function'){
                    input.inits.push(check.init);
                }
                if (isLast) {
                    input.parsed.call(undefined, {
                        exists: true,
                        type: typeof check,
                        obj: check,
                        inits: input.inits
                    });
                } else {
                    Utils.parseRoute({
                        path: paths.join(delimiter),
                        target: check,
                        delimiter: delimiter,
                        parsed: input.parsed,
                        inits: input.inits
                    });
                }
            } else {
                input.parsed.call(undefined, {
                    exists: false
                });
            }
        },
        route: function(){

            Utils.parseRoute({
                path: Utils.settings.meta.route,
                target: Routes,
                delimiter: '/',
                parsed: function(res) {
                    if(res.exists && res.type=='function'){
                        if(res.inits.length!=0){
                            for(var i in res.inits){
                                res.inits[i].call();
                            }
                        }
                        res.obj.call();
                    }
                }
            });

        },
        clone: []
    };
    var _log = Utils.log;

    /* -----------------------------------------
       AJAX
    ----------------------------------------- */
    Ajax = {
        send: function(type, url, data, returnFunc){
            $.ajax({
                type: type,
                url: url,
                dataType: 'json',
                data: data,
                success: returnFunc
            });
        },
        call: function(url, data, returnFunc) {
            Ajax.send('POST', url, data, returnFunc);
        },
        get: function(url, data, returnFunc) {
            Ajax.send('GET', url, data, returnFunc);
        },
        facets: false
    };

    /* -----------------------------------------
       EVENTS
    ----------------------------------------- */
    Events = {
        endpoints: {
            serializeHistogram: function(e, arr) {
                var name = $(this).attr('data-name');
                var facet = Utils.settings.facets[name];
                var field = facet.date_histogram.field;
                Query.holder[name] = {};

                var value = $(this).val();
                if (!value) {
                    return;
                }
                var values = value.split(',');
                if (values.length != 2) {
                    return;
                }

                var entries = Ajax.facets[name].entries;
                if (entries[values[0]] == undefined || entries[values[0]].time == undefined) {
                    values[0] = entries[0].time;
                } else {
                    values[0] = entries[values[0]].time;
                }
                if (entries[values[1]] == undefined || entries[values[1]].time == undefined) {
                    values[1] = entries[entries.length - 1].time;
                } else {
                    values[1] = entries[values[1]].time;
                }

                var query = $("#facetly-form ul#facet-"+name+" :input").serializeObject();

                var i = 0;
                for (q in query[name]) {

                    var operator = query[name][q].operator;

                    if (operator != '' && values[0] != '' && values[1] != '') {

                        if (Query.holder[name][operator] == undefined) Query.holder[name][operator] = [];


                        var query = {};
                        query['range'] = {};
                        query['range'][field] = {
                            from: parseInt(values[0]),
                            to: parseInt(values[1])
                        };
                        if (facet['nested']) {
                            var object = {
                                nested: {
                                    path: facet['nested'],
                                    query: query
                                }
                            };
                        } else {
                            var object = query;
                        }
                        Query.holder[name][operator].push(object);
                        i++;
                    }
                }
                App.loadResults();
            },
            serializeTerms: function(e) {
                var name = $(this).attr('data-name');
                var query = $("#facetly-form ul#facet-"+name+" :input").serializeObject();
                var facet = Utils.settings.facets[name];
                var field = facet.terms.field;
                Query.holder[name] = {};
                var i = 0;
                for (q in query[name]) {

                    var operator = query[name][q].operator;
                    var value = query[name][q].value;

                    if (operator != '' && value != '') {

                        if (Query.holder[name][operator] == undefined) Query.holder[name][operator] = [];

                        // Check if nested
                        if (facet['nested']) {
                            var object = {
                                nested: {
                                    path: facet['nested'],
                                    query: {
                                        query_string: {}
                                    }
                                }
                            };
                            object.nested.query.query_string['default_field'] = field;
                            object.nested.query.query_string['query'] = value;
                        } else {
                            var object = {
                                query_string: {}
                            };
                            object.query_string['default_field'] = field;
                            object.query_string['query'] = value;
                        }
                        Query.holder[name][operator].push(object);
                        i++;
                    }
                }
                App.loadResults();
            },
            clone: function(e) {
                var li = $(this).closest('li');
                var name = $(this).attr('data-name');
                var cloneables = $("li[data-clonable='facetly-"+name+"']");
                var firstLi = cloneables.first();
                var firstLiHTML = firstLi[0].outerHTML;

                if (Utils.clone[name] == undefined) Utils.clone[name] = cloneables.length;

                Utils.clone[name] = Utils.clone[name] + 1;

                var index = eval("(" + decodeURIComponent($(this).attr('data-index')) + ")");
                for (i in index) {
                    var pattern = new RegExp(RegExp.quote(index[i].orig), 'g');
                    firstLiHTML = firstLiHTML.replace(pattern, index[i].format.replace("{#}", Utils.clone[name]));
                }
                // Remove bound
                var pattern = new RegExp(RegExp.quote('data-bound="true"'), 'g');
                firstLiHTML = firstLiHTML.replace(pattern, '');

                $(firstLi).after(firstLiHTML);
                // Rebind events
                Events.bindEvents();
                return;
            },
            remove: function(e) {
                var li = $(this).closest('li');
                var ul = $(li).parent();

                // Check custom count
                if ($('li.custom', ul).length == 1) {
                    return false;
                }

                $(li).remove();
                Events.bindEvents();
            }
        },
        serialize: function() {
            var query = {bool: {}};

            query.bool['must'] = [];
            query.bool['should'] = [];
            query.bool['must_not'] = [];

            var inc = 0;
            for (i in Query.holder) {
                for (ii in Query.holder[i]) {
                    for (iii in Query.holder[i][ii]) {
                        query.bool[ii].push(Query.holder[i][ii][iii]);
                        inc++;
                    }
                }
            }
            var query = inc == 0 ? Query.matchAllQuery() : query;

            // Set current query
            Query.currentQuery = query;

            var object = {query: query, size: Utils.settings.perPage};
            var string = Query.create(query);
            if (Utils.settings.onSerialize) Utils.settings.onSerialize(object, string);
            return object;
        },
        bindEvents: function(){
            _log('Binding Events');

            $('[data-event]').each(function() {
                var _this = this,
                    method = _this.dataset.method || 'click',
                    name = _this.dataset.event,
                    bound = _this.dataset.bound;

                if (!bound) {
                    Utils.parseRoute({
                        path: name,
                        target: Events.endpoints,
                        delimiter: '.',
                        parsed: function(res) {
                            if(res.exists){
                                _this.dataset.bound = true;
                                $(_this).on(method, function(e){
                                    res.obj.call(_this, e);
                                });
                           }
                        }
                    });
                }
            });
            _log('Events Bound');
        },
        init: function(){
            Events.bindEvents();
        }
    };

    /* -----------------------------------------
       TEMPLATES
    ----------------------------------------- */
    Templates = {
        init: function() {
            _log('Compiling templates');
            Templates.types.terms = Handlebars.compile(Templates.types.terms);
            Templates.types.date_histogram = Handlebars.compile(Templates.types.date_histogram);
            // Random helper
            Handlebars.registerHelper('random', function() {
                var randLetter = String.fromCharCode(65 + Math.floor(Math.random() * 26));
                var uniqid = randLetter + Date.now();
                return uniqid;
            });
            // Lang helper
            Handlebars.registerHelper('trans', function(key, vars) {
                return Lang.get(key, vars);
            });
            // Increment helper
            Handlebars.registerHelper('unique_inc', function(bool) {
                return val + 1;
            });
            // Increment helper
            Handlebars.registerHelper('inc', function(val) {
                return val + 1;
            });
            // Type helper
            Handlebars.registerHelper('type', function(facet, name) {
                var template = Templates.types[facet._type];
                // if (Utils.settings.facets[name].nested != undefined) template = Templates.types['nested'];
                return new Handlebars.SafeString(template({facet: facet, name: name}));
            });
            // Facets helper
            Handlebars.registerHelper('facets', function(name, options) {
                return options.fn(Utils.settings.facets[name]);
            });
            // Thead helper
            Handlebars.registerHelper('thead', function(results) {
                var html = '<tr>';
                for (i in results.hits.hits) {
                    for (key in results.hits.hits[i]._source) {
                        if (jQuery.inArray(key, Utils.settings.excludedFields) === -1) {
                            html += '<th>'+key+'</th>';
                        }
                    }
                    break;
                }
                html += '</tr>';
                return new Handlebars.SafeString(html);
            });
            // JSON helper
            Handlebars.registerHelper('json', function(key, context) {
                if (jQuery.inArray(context.data.key, Utils.settings.excludedFields) === -1) {
                    if (typeof key == 'object') {
                        var html = JSON.stringify(key);
                    } else {
                        var html = key;
                    }
                    return new Handlebars.SafeString("<td>" + html + "</td>");
                }
            });
            Templates.search = Handlebars.compile(Templates.search);
            Templates.facets = Handlebars.compile(Templates.facets);
            Templates.results = Handlebars.compile(Templates.results);
            _log('Templates Compiled');
        },
        types: {
            terms: '<ul id="facet-{{name}}"> \
                <li class="custom" data-clonable="facetly-{{name}}"> \
                    <div class="form-inline form-group"> \
                        <select class="input-small" name="{{name}}[0][operator]" data-type="operator" data-name="{{name}}" data-event="serializeTerms" data-method="change"> \
                            <!--<option value=""></option>--> \
                            <option value="must">{{trans "must"}}</option> \
                            <option value="should">{{trans "should"}}</option> \
                            <option value="must_not">{{trans "must_not"}}</option> \
                        </select> \
                        <div class="input-group"> \
                            <input class="input-small form-control" name="{{name}}[0][value]" type="text" data-name="{{name}}" data-type="value" data-event="serializeTerms" data-method="keyup"> \
                            <a href="javascript:void()" class="input-group-addon" data-event="clone" data-index="%5B%7Borig%3A%20%27{{name}}%5B0%5D%5Boperator%5D%27%2C%20format%3A%20%27{{name}}%5B%7B%23%7D%5D%5Boperator%5D%27%7D%2C%20%7Borig%3A%20%27{{name}}%5B0%5D%5Bvalue%5D%27%2C%20format%3A%20%27{{name}}%5B%7B%23%7D%5D%5Bvalue%5D%27%7D%5D" data-name="{{name}}" data-method="click"><span class="glyphicon glyphicon-plus"></span></a> \
                            <a href="javascript:void()" class="input-group-addon" data-event="remove" data-name="{{name}}" data-method="click"><span class="glyphicon glyphicon-trash"></span></a> \
                        </div> \
                    </div> \
                </li> \
                {{#each facet.terms}} \
                    <li data-clonable="facetly-{{../name}}"> \
                        <div class="form-inline form-group"> \
                            <select class="input-small" name="{{../name}}[{{inc @index}}][operator]" data-name="{{../name}}" data-event="serializeTerms" data-method="change"> \
                                <!--<option value=""></option>--> \
                                <option value=""></option> \
                                <option value="must">{{trans "must"}}</option> \
                                <option value="should">{{trans "should"}}</option> \
                                <option value="must_not">{{trans "must_not"}}</option> \
                            </select> \
                            <input class="input-small form-control" type="text" value="{{this.term}}" name="{{../name}}[{{inc @index}}][value]" readonly="readonly" data-event="serializeTerms" data-method="keyup"> \
                            <small>({{this.count}})</small> \
                        </div> \
                    </li> \
                {{/each}} \
            </ul>',
            date_histogram: '<ul id="facet-{{name}}"> \
                <li class="custom" data-clonable="facetly-{{name}}"> \
                    <div id="facetly-slider-graph-{{name}}-0"></div> \
                    <div class="form-inline form-group"> \
                        <select class="input-small" name="{{name}}[0][operator]" data-type="operator" data-name="{{name}}" data-event="serializeHistogram" data-method="change"> \
                            <!--<option value=""></option>--> \
                            <option value="must">{{trans "must"}}</option> \
                            <option value="should">{{trans "should"}}</option> \
                            <option value="must_not">{{trans "must_not"}}</option> \
                        </select> \
                        <div class="slide-wrapper"> \
                            <input type="text" class="input-small form-control" name="{{name}}[0][value]" data-name="{{name}}" id="facetly-slider-{{name}}-0" value="" data-slider-min="0" data-slider-max="{{facet.entries.length}}" data-slider-step="1" data-slider-value="[0, {{facet.entries.length}}]" data-slider-selection="after" data-slider-tooltip="hide" data-event="serializeHistogram" method="change"> \
                        </div> \
                        <!-- <div class="btn-group"> \
                            <a href="javascript:void()" class="btn btn-mini" data-src="facetly-clonable-{{name}}" data-index="alert(\'TODO\')" data-event="clone" data-name="{{name}}" data-method="click"><span class="glyphicon glyphicon-plus"></span></a> \
                            <a href="javascript:void()" class="btn btn-mini" data-event="remove" data-name="{{name}}" data-method="click"><span class="glyphicon glyphicicon-trash"></span></a> \
                        </div> --> \
                    </div> \
                    <script> \
                    var values = new Array(); \
                    {{#each facet.entries}} \
                    values.push({ \
                        time: {{this.time}}, \
                        count: {{this.count}} \
                    }); \
                    {{/each}} \
                    $("#facetly-slider-{{name}}-0").slider().on("slideStop", function(ev){ \
                        $("#facetly-slider-{{name}}-0").trigger("click", [{}]); \
                    }); \
                    </script> \
                </li> \
            </ul>',
        },
        search: '<div class="well"> \
            <form class="form-horizontal"> \
                <fieldset> \
                    <legend>{{trans "search"}} <small>(<span class="nbresults">0</span> {{trans "results"}})</small></legend> \
                    <div class="control-group"> \
                        <label class="control-label" for="must">{{trans "must"}}</label> \
                        <div class="controls"> \
                            <div id="search_must" class="search"></div> \
                        </div> \
                    </div> \
                    <div class="control-group"> \
                        <label class="control-label" for="should">{{trans "should"}}</label> \
                        <div class="controls"> \
                            <div id="search_should" class="search"></div> \
                        </div> \
                    </div> \
                    <div class="control-group"> \
                        <label class="control-label" for="must_not">{{trans "must_not"}}</label> \
                        <div class="controls"> \
                            <div id="search_must_not" class="search"></div> \
                        </div> \
                    </div> \
                </fieldset> \
            </form> \
        </div>',
        results: '<div> \
              {{#each results.hits.hits}} \
              <div class="panel panel-info"> \
                  <div class="panel-heading"> \
                      <a href="{{this._source.url}}" target="_blank">{{this._source.url}}</a> \
                  </div> \
                  <div class="panel-heading"> \
                      <b>To:</b> {{this._source.recipients}} \
                  </div> \
                  <div class="panel-body"> \
                      <input class="read-more" type="checkbox" id="toggle-{{this._id}}"> \
                      <div class="preview"> \
                         {{{this._source.preview}}}... \
                         <label class="toggle-label" for="toggle-{{this._id}}">Show full letter</label> \
                      </div> \
                      <div class="full-text"> \
                         <label class="toggle-label" for="toggle-{{this._id}}">Hide full text</label> \
                         {{{this._source.text}}} \
                      </div> \
                  </div> \
                  <div class="panel-footer"> \
                      {{{this._source.signatures}}} \
                  </div> \
              </div> \
              {{else}} \
                  <div>{{trans "no_results"}}</div> \
              {{/each}} \
        </div> \
        <p>{{results.hits.total}} {{trans "results"}}</p>',
        facets: '<form id="facetly-form"> \
            <ul> \
                {{#each facets}} \
                    <li> \
                        <div class="header"> \
                            {{@key}} \
                            {{#if this.total}} \
                            <small>{{trans "total"}}: {{this.total}}</small> \
                            {{/if}} \
                            {{#if this.entries}} \
                            <small>{{trans "total"}}: {{this.entries.length}}</small> \
                            {{/if}} \
                            {{#if this.other}} \
                            <small>{{trans "other"}}: {{this.other}}</small> \
                            {{/if}} \
                        </div> \
                        <div class="content"> \
                            {{type this @key}} \
                        </div> \
                    </li> \
                {{/each}} \
            </ul> \
        </form> \
        <script> \
        $( "'+Utils.settings.selector+' ul" ).accordion({ \
            header: "> li > .header", \
            heightStyle: "content" \
        }); \
        </script>'
    };

    /* -----------------------------------------
       INTERFACE
    ----------------------------------------- */
    UI = {
        init: function() {
            UI.row1 = Handlebars.compile(UI.row1);
            UI.row1 = $(UI.row1());

            UI.search   = Handlebars.compile(UI.search);
            UI.search   = $(UI.search());

            element.append(UI.row1);
            UI.row1.append(UI.search);

            UI.row2 = Handlebars.compile(UI.row2);
            UI.row2 = $(UI.row2());

            UI.sidebar   = Handlebars.compile(UI.sidebar);
            UI.sidebar   = $(UI.sidebar());

            UI.results   = Handlebars.compile(UI.results);
            UI.results   = $(UI.results());

            element.append(UI.row2);
            UI.row2.append(UI.sidebar);
            UI.row2.append(UI.results);
        },
        row1: '<div class="row-fluid" style="display: none;"></div>',
        row2: '<div class="row-fluid"></div>',
        search: '<div class="col-xs-12"></div>',
        sidebar: '<div class="sidebar col-xs-4"></div>',
        results: '<div class="results col-xs-8"></div>'
    };

    /* -----------------------------------------
       LANGUAGE
    ----------------------------------------- */
    Lang = {
        locale: 'en',
        get: function(key, vars) {
            return Lang.translations[Lang.locale][key];
        },
        translations: {
            en: {
                must: 'Must',
                should: 'Should',
                must_not: 'Must Not',
                total: 'Total',
                other: 'Others',
                search: 'Search',
                results: 'results',
                no_results: 'No results found',
            },
            it: {
                must: 'Deve',
                should: 'Può',
                must_not: 'Non Deve',
                total: 'Totale',
                other: 'Altri',
                search: 'Ricerca',
                results: 'risultati',
                no_results: 'Nessun risultato',
            }
        }
    };

    /* -----------------------------------------
       QUERY
    ----------------------------------------- */
    Query = {
        create: function(query) {
            return JSON.stringify(query)
        },
        matchAllQuery: function() {
            var query = {};
            query['match_all'] = {};
            return query;
        },
        holder: {},
        currentQuery: {}
    };

    /* -----------------------------------------
       APP
    ----------------------------------------- */
    App = {
        logic: {},
        init: function(settings) {
            _log('Initializing Facetly');
            Utils.settings.init(settings);
            UI.init();
            Templates.init();
            _log('Initialized Facetly');

            // Dirty hack for cache
            Utils.cache.window.tmp = {};

            // Get facets
            App.loadFacets(function() {
                Events.init();

                // Get results
                App.loadResults(function(data) {
                    Events.init();
                    $(Utils.settings.selector + ' .nbresults').html(data.hits.total || 0);
                });
            });
        },
        loadFacets: function(callback) {
            _log('Getting Facets');
            Ajax.call(Utils.elastic_search_url(), Query.create({facets: Utils.settings.facets, query: Query.matchAllQuery}), function(data) {
                UI.sidebar.html(Templates.facets({facets: data.facets }));
                Ajax.facets = data.facets;

                // Get search
                UI.search.html(Templates.search());

                var facets = {};
                var values = {};
                for (name in data.facets) {
                    // Facets
                    var facet = data.facets[name];
                    // Only term facets are allowed
                    // as visualsearch plugin can handle
                    // only key value searches
                    if (!facet.terms) {
                        continue;
                    }
                    facets[name] = facet;
                    // Values
                    if (values[name] == undefined) {
                        values[name] = [];
                    }
                    for (i in facet.terms) {
                        var term = facet.terms[i].term;
                        values[name].push(term);   
                    }
                }

                var facetMatches = function(callback) {
                    callback(Object.keys(facets));
                };

                var valueMatches = function(facet, searchTerm, callback) {
                    callback(values[facet]);
                };

                // Search Must
                var visualSearch = VS.init({
                  container : $(Utils.settings.selector + ' #search_must'),
                  query     : '',
                  callbacks : {
                    search       : function(query, searchCollection) {},
                    facetMatches : facetMatches,
                    valueMatches : valueMatches,
                  }
                });

                // Search Should
                var visualSearch = VS.init({
                  container : $(Utils.settings.selector + ' #search_should'),
                  query     : '',
                  callbacks : {
                    search       : function(query, searchCollection) {},
                    facetMatches : facetMatches,
                    valueMatches : valueMatches,
                  }
                });

                // Search Must Not
                var visualSearch = VS.init({
                  container : $(Utils.settings.selector + ' #search_must_not'),
                  query     : '',
                  callbacks : {
                    search       : function(query, searchCollection) {},
                    facetMatches : facetMatches,
                    valueMatches : valueMatches,
                  }
                });

                _log('Facets Loaded');
                if (callback) callback();
            });
        },
        loadResults: function(callback) {
            _log('Loading Results');
            Ajax.call(Utils.elastic_search_url(), Query.create(Events.serialize()), function(data) {
                for (var i = 0; i < data.hits.hits.length ; i ++) {
                    var d = data.hits.hits[i]._source;
                    if (d.text) {
                        d.text = d.text.replace(/\n+/g, '<br><br>');
                        d.preview = d.text.slice(0, 500);
                        d.remainder = d.text.slice(500);
                    }
                }
                UI.results.html(Templates.results({results: data}));
                $(Utils.settings.selector + ' .nbresults').html(data.hits.total || 0);
                _log('Results Loaded');
                if (callback) callback(data);
            });
        }
    };
    var element;

    /* -----------------------------------------
       PUBLIC
    ----------------------------------------- */
    Public = {
        init: function(settings) {
            App.init(settings);
        },
        loadFacets: App.loadFacets,
        templates: App.Templates,
        currentQuery: Query.currentQuery
    };

    return Public;

})(window.jQuery);

// RegExp quotes
RegExp.quote = function(str) {
    return (str+'').replace(/([.?*+^$[\]\\(){}|-])/g, "\\$1");
};

readMore = function(el) {
  debugger;
};

// Serialize Object
// https://github.com/macek/jquery-serialize-object
(function(e){e.fn.serializeObject=function(){var t=this,n={},r={},i={validate:/^[a-zA-Z][a-zA-Z0-9_]*(?:\[(?:\d*|[a-zA-Z0-9_]+)\])*$/,key:/[a-zA-Z0-9_]+|(?=\[\])/g,push:/^$/,fixed:/^\d+$/,named:/^[a-zA-Z0-9_]+$/};this.build=function(e,t,n){e[t]=n;return e};this.push_counter=function(e){if(r[e]===undefined){r[e]=0}return r[e]++};e.each(e(this).serializeArray(),function(){if(!i.validate.test(this.name)){return}var r,s=this.name.match(i.key),o=this.value,u=this.name;while((r=s.pop())!==undefined){u=u.replace(new RegExp("\\["+r+"\\]$"),"");if(r.match(i.push)){o=t.build([],t.push_counter(u),o)}else if(r.match(i.fixed)){o=t.build([],r,o)}else if(r.match(i.named)){o=t.build({},r,o)}}n=e.extend(true,n,o)});return n}})(jQuery)
