# Copyright 2017 The Chromium Authors. All rights reserved.
# Use of this source code is governed by a BSD-style license that can be
# found in the LICENSE file.

import common
from common import TestDriver
from common import IntegrationTest


class LoFi(IntegrationTest):

  #  Checks that the compressed image is below a certain threshold.
  #  The test page is uncacheable otherwise a cached page may be served that
  #  doesn't have the correct via headers.
  def testLoFi(self):
    with TestDriver() as test_driver:
      test_driver.AddChromeArg('--enable-spdy-proxy-auth')
      test_driver.AddChromeArg('--data-reduction-proxy-lo-fi=always-on')
      # Disable server experiments such as tamper detection.
      test_driver.AddChromeArg('--data-reduction-proxy-server-experiments-'
                               'disabled')

      test_driver.LoadURL('http://check.googlezip.net/static/index.html')

      lofi_responses = 0
      for response in test_driver.GetHTTPResponses():
        if not response.url.endswith('png'):
          continue
        if not response.request_headers:
          continue
        if (self.checkLoFiResponse(response, True)):
          lofi_responses = lofi_responses + 1

      # Verify that Lo-Fi responses were seen.
      self.assertNotEqual(0, lofi_responses)

  # Checks that Lo-Fi placeholder images are not loaded from cache on page
  # reloads when Lo-Fi mode is disabled or data reduction proxy is disabled.
  # First a test page is opened with Lo-Fi and chrome proxy enabled. This allows
  # Chrome to cache the Lo-Fi placeholder image. The browser is restarted with
  # chrome proxy disabled and the same test page is loaded. This second page
  # load should not pick the Lo-Fi placeholder from cache and original image
  # should be loaded. Finally, the browser is restarted with chrome proxy
  # enabled and Lo-Fi disabled and the same test page is loaded. This third page
  # load should not pick the Lo-Fi placeholder from cache and original image
  # should be loaded.
  def testLoFiCacheBypass(self):
    with TestDriver() as test_driver:
      # First page load, enable Lo-Fi and chrome proxy. Disable server
      # experiments such as tamper detection. This test should be run with
      # --profile-type=default command line for the same user profile and cache
      # to be used across the two page loads.
      test_driver.AddChromeArg('--enable-spdy-proxy-auth')
      test_driver.AddChromeArg('--data-reduction-proxy-lo-fi=always-on')
      test_driver.AddChromeArg('--profile-type=default')
      test_driver.AddChromeArg('--data-reduction-proxy-server-experiments-'
                               'disabled')

      test_driver.LoadURL('http://check.googlezip.net/cacheable/test.html')

      lofi_responses = 0
      for response in test_driver.GetHTTPResponses():
        if not response.url.endswith('png'):
          continue
        if not response.request_headers:
          continue
        if (self.checkLoFiResponse(response, True)):
          lofi_responses = lofi_responses + 1

      # Verify that Lo-Fi responses were seen.
      self.assertNotEqual(0, lofi_responses)

      # Second page load with the chrome proxy off.
      test_driver._StopDriver()
      test_driver.RemoveChromeArg('--enable-spdy-proxy-auth')
      test_driver.LoadURL('http://check.googlezip.net/cacheable/test.html')

      responses = 0
      for response in test_driver.GetHTTPResponses():
        if not response.url.endswith('png'):
          continue
        if not response.request_headers:
          continue
        responses = responses + 1
        self.assertNotHasChromeProxyViaHeader(response)
        self.checkLoFiResponse(response, False)

      # Verify that responses were seen.
      self.assertNotEqual(0, responses)

      # Third page load with the chrome proxy on and Lo-Fi off.
      test_driver._StopDriver()
      test_driver.AddChromeArg('--enable-spdy-proxy-auth')
      test_driver.RemoveChromeArg('--data-reduction-proxy-lo-fi=always-on')
      test_driver.AddChromeArg('--data-reduction-proxy-lo-fi=disabled')
      test_driver.LoadURL('http://check.googlezip.net/cacheable/test.html')

      responses = 0
      for response in test_driver.GetHTTPResponses():
        if not response.url.endswith('png'):
          continue
        if not response.request_headers:
          continue
        responses = responses + 1
        self.assertHasChromeProxyViaHeader(response)
        self.checkLoFiResponse(response, False)

      # Verify that responses were seen.
      self.assertNotEqual(0, responses)

if __name__ == '__main__':
  IntegrationTest.RunAllTests()
