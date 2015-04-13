/*jshint node: true, camelcase: false*/
/*globals module: true*/

module.exports = function(grunt) {
  grunt.initConfig({
    //bower_concat: {
    //  all: {
    //    dest: 'dist/js/calaca.js',
    //    mainFiles: {
    //      "calaca": ["js/app.js", "js/controllers.js", "js/services.js"],
    //      "elasticsearch": ["elasticsearch.angular.js"]
    //    }
    //  }
    //},
    concat: {
      all: {
        files: {
          'dist/js/legisletters.js': [
            'bower_components/markdown/lib/markdown.js',
            'bower_components/angular/angular.min.js',
            'bower_components/angular-animate/angular-animate.min.js',
            'bower_components/elasticsearch/elasticsearch.angular.min.js',
            'src/js/*'
          ]
        }
      }
    },
    copy: {
      all: {
        cwd: 'src',
        src: ['css/legisletters.css', 'index.html'],
        dest: 'dist',
        expand: true
      }
    }
  });
  //grunt.loadNpmTasks('grunt-bower-concat');
  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-copy');

  grunt.registerTask('default', ['copy', 'concat']);
};
