fin Utility Library [![Build Status](https://travis-ci.org/stestagg/fin.svg?branch=master)](https://travis-ci.org/stestagg/fin)
===================

A collection of useful Python modules providing utility and testing functionality.

Basic Module Overview
----------------------

 * `fin.cache`
  * A lightweight, unobtrusive method/property caching model, exposed as a set of decorators
 * `fin.color`
  * Provides VT-100 style string formatting, with graceful fallbacks for non-terminal output
 * `fin.contextlog`
  * Basic stdout/stderr logging context managers
 * `fin.named`
  * A namedtuple implementation for python 2.5 (defers to builtin implementation when available)
 * `fin.string`
  * Simple string subclass providing some extra methods
 * `fin.module`
  * Module import/finding/searching functions
