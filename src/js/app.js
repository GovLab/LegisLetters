/*
 * LegisLetters - Search UI for Elasticsearch
 * https://github.com/romansanchez/LegisLetters
 * http://romansanchez.me
 * @rooomansanchez
 * 
 * v1.1.1
 * MIT License
 */

/*jslint browser: true*/
/*globals angular*/

/* Module */
window.LegisLetters = angular.module('legisletters',
                                     ['elasticsearch', 'ngAnimate'],
    ['$locationProvider', function($locationProvider){
        $locationProvider.html5Mode(true);
    }]
);
