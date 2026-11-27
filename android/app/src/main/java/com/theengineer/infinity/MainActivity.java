package com.theengineer.infinity;

import android.annotation.SuppressLint;
import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.view.KeyEvent;
import android.view.View;
import android.view.Window;
import android.webkit.CookieManager;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.LinearLayout;
import android.widget.ProgressBar;

/**
 * Infinity — a thin, full-screen shell around the live, auto-updating platform.
 * The page itself is served by GitHub Pages and refreshed by GitHub Actions;
 * this app only renders it, opens outside links in the phone browser, and shows
 * a retry panel when there is no connection.
 */
public class MainActivity extends Activity {

    private static final String HOME = "https://engraymanfm-oss.github.io/infinity-platform/";
    private static final String SITE_HOST = "engraymanfm-oss.github.io";

    /** Links in the page use target="_blank"; dropping it lets shouldOverrideUrlLoading see the click. */
    private static final String EXTERNAL_JS =
            "(function(){var fix=function(){try{document.querySelectorAll('a[target=\"_blank\"]')"
            + ".forEach(function(a){a.removeAttribute('target');});}catch(e){}};fix();"
            + "try{var t=null;new MutationObserver(function(){clearTimeout(t);t=setTimeout(fix,400);})"
            + ".observe(document.documentElement,{childList:true,subtree:true});}catch(e){}})();";

    private WebView web;
    private ProgressBar progress;
    private LinearLayout errorPanel;

    @SuppressLint("SetJavaScriptEnabled")
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);

        Window window = getWindow();
        window.setStatusBarColor(Color.parseColor("#00224B"));
        window.setNavigationBarColor(Color.parseColor("#050506"));

        web = findViewById(R.id.web);
        progress = findViewById(R.id.progress);
        errorPanel = findViewById(R.id.errorPanel);
        Button retry = findViewById(R.id.retry);

        WebSettings s = web.getSettings();
        s.setJavaScriptEnabled(true);
        s.setDomStorageEnabled(true);
        s.setDatabaseEnabled(true);
        s.setUseWideViewPort(true);
        s.setLoadWithOverviewMode(true);
        s.setSupportZoom(false);
        s.setBuiltInZoomControls(false);
        s.setDisplayZoomControls(false);
        s.setMediaPlaybackRequiresUserGesture(false);
        s.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        s.setCacheMode(WebSettings.LOAD_DEFAULT);
        s.setUserAgentString(s.getUserAgentString() + " InfinityApp/1.0");

        CookieManager.getInstance().setAcceptCookie(true);
        web.setBackgroundColor(Color.parseColor("#050506"));
        web.setOverScrollMode(View.OVER_SCROLL_NEVER);

        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                return handleUrl(request.getUrl());
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView view, String url) {
                return handleUrl(Uri.parse(url));
            }

            @Override
            public void onPageFinished(WebView view, String url) {
                progress.setVisibility(View.GONE);
                errorPanel.setVisibility(View.GONE);
                view.evaluateJavascript(EXTERNAL_JS, null);
            }

            @Override
            public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                if (request.isForMainFrame()) {
                    showError();
                }
            }
        });

        web.setWebChromeClient(new WebChromeClient() {
            @Override
            public void onProgressChanged(WebView view, int newProgress) {
                progress.setProgress(newProgress);
                progress.setVisibility(newProgress >= 100 ? View.GONE : View.VISIBLE);
            }
        });

        retry.setOnClickListener(v -> loadHome());
        loadHome();
    }

    private void loadHome() {
        errorPanel.setVisibility(View.GONE);
        progress.setVisibility(View.VISIBLE);
        web.loadUrl(HOME);
    }

    private void showError() {
        progress.setVisibility(View.GONE);
        errorPanel.setVisibility(View.VISIBLE);
    }

    /** Same site stays inside the app; every other http(s) link opens in the phone browser. */
    private boolean handleUrl(Uri uri) {
        if (uri == null) {
            return true;
        }
        String scheme = uri.getScheme() == null ? "" : uri.getScheme().toLowerCase();
        String host = uri.getHost() == null ? "" : uri.getHost().toLowerCase();

        if (("http".equals(scheme) || "https".equals(scheme)) && SITE_HOST.equals(host)) {
            return false;
        }
        if ("http".equals(scheme) || "https".equals(scheme) || "mailto".equals(scheme)
                || "tel".equals(scheme) || "intent".equals(scheme)) {
            try {
                startActivity(new Intent(Intent.ACTION_VIEW, uri));
            } catch (Exception ignored) {
                // no app able to handle it: keep the user on the platform
            }
        }
        return true;
    }

    @Override
    public boolean onKeyDown(int keyCode, KeyEvent event) {
        if (keyCode == KeyEvent.KEYCODE_BACK && web != null && web.canGoBack()) {
            web.goBack();
            return true;
        }
        return super.onKeyDown(keyCode, event);
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (web != null) {
            web.onResume();
        }
    }

    @Override
    protected void onPause() {
        if (web != null) {
            web.onPause();
        }
        super.onPause();
    }

    @Override
    protected void onDestroy() {
        if (web != null) {
            web.destroy();
        }
        super.onDestroy();
    }
}
