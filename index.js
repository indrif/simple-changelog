'use strict'

const stream = require('stream')
const gitRawCommits = require('git-raw-commits')
const mergeConfig = require('conventional-changelog-core/lib/merge-config')
const conventionalCommitsParser = require('conventional-commits-parser')
const conventionalChangelogWriter = require('conventional-changelog-writer')
const through = require('through2')
var quinyx = require('conventional-changelog-quinyx')
var fs = require('fs')
var accessSync = require('fs-access').sync
var chalk = require('chalk')
var figures = require('figures')
var sprintf = require('sprintf-js').sprintf

function conventionalChangelogRaw (options, context, gitRawCommitsOpts, parserOpts, writerOpts, execOpts) {
  writerOpts = writerOpts || {}

  var readable = new stream.Readable({
    objectMode: writerOpts.includeDetails
  })
  readable._read = function () {}

  mergeConfig(options, context, gitRawCommitsOpts, parserOpts, writerOpts)
    .then(function (data) {
      options = data.options
      context = data.context
      gitRawCommitsOpts = data.gitRawCommitsOpts
      parserOpts = data.parserOpts
      writerOpts = data.writerOpts

      gitRawCommits(gitRawCommitsOpts, execOpts)
        .on('error', function (err) {
          err.message = 'Error in git-raw-commits: ' + err.message
          setImmediate(readable.emit.bind(readable), 'error', err)
        })
        .pipe(conventionalCommitsParser(parserOpts))
        .on('error', function (err) {
          err.message = 'Error in conventional-commits-parser: ' + err.message
          setImmediate(readable.emit.bind(readable), 'error', err)
        })
        .pipe(through.obj(function (chunk, enc, cb) {
          try {
            options.transform.call(this, chunk, cb)
          } catch (err) {
            cb(err)
          }
        }))
        .on('error', function (err) {
          err.message = 'Error in options.transform: ' + err.message
          setImmediate(readable.emit.bind(readable), 'error', err)
        })
        .pipe(conventionalChangelogWriter(context, writerOpts))
        .on('error', function (err) {
          err.message = 'Error in conventional-changelog-writer: ' + err.message
          setImmediate(readable.emit.bind(readable), 'error', err)
        })
        .pipe(through({
          objectMode: writerOpts.includeDetails
        }, function (chunk, enc, cb) {
          try {
            readable.push(chunk)
          } catch (err) {
            setImmediate(function () {
              throw err
            })
          }

          cb()
        }, function (cb) {
          readable.push(null)

          cb()
        }))
    })
    .catch(function (err) {
      setImmediate(readable.emit.bind(readable), 'error', err)
    })

  return readable
}

function conventionalChangelog (options, context, gitRawCommitsOpts, parserOpts, writerOpts, execOpts) {
  options = options || {}
  options.config = quinyx
  return conventionalChangelogRaw(options, context, gitRawCommitsOpts, parserOpts, writerOpts, execOpts)
}

conventionalChangelog.createIfMissing = function (infile) {
  try {
    accessSync(infile, fs.F_OK)
  } catch (err) {
    if (err.code === 'ENOENT') {
      conventionalChangelog.checkpoint('created %s', [infile])
      fs.writeFileSync(infile, '\n', 'utf-8')
    }
  }
}

conventionalChangelog.checkpoint = function (msg, args) {
  console.info(chalk.green(figures.tick) + ' ' + sprintf(msg, args.map(function (arg) {
    return chalk.bold(arg)
  })))
}

module.exports = conventionalChangelog
