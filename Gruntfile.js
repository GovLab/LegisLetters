/*jshint node: true, camelcase: false*/
/*globals module: true*/

module.exports = function(grunt) {
  grunt.initConfig({
    bower_concat: {
      all: {
        dest: 'dist/js/calaca.js',
        mainFiles: {
          "calaca": ["js/app.js", "js/controllers.js", "js/services.js"]
        }
      }
    },
    concat: {
      all: {
        files: {
          'dist/css/legisletters.css': ['bower_components/calaca/css'],
          'dist/js/legisletters.js': ['src/js/*', 'dist/js/calaca.js']
        }
      }
    },
    copy: {
      all: {
        cwd: 'src',
        src: '**',
        dest: 'dist',
        expand: true
      }
    }
  });
  grunt.loadNpmTasks('grunt-bower-concat');
  grunt.loadNpmTasks('grunt-contrib-concat');
  grunt.loadNpmTasks('grunt-contrib-copy');

  grunt.registerTask('default', ['copy', 'bower_concat', 'concat']);
};
