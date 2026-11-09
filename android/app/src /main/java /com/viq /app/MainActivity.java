package com.viq.app;

import android.Manifest;
import android.app.Activity;
import android.app.AlertDialog;
import android.app.DownloadManager;
import android.content.Intent;
import android.content.pm.PackageManager;
import android.net.Uri;
import android.os.Bundle;
import android.os.Environment;
import android.view.View;
import android.webkit.*;
import android.widget.LinearLayout;
import android.widget.ProgressBar;
import android.widget.Toast;
import java.util.ArrayList;

public class MainActivity extends Activity {
    private WebView web;
    private ValueCallback<Uri[]> fileCallback;
    private PermissionRequest mediaRequest;
    private static final int FILE_PICK = 41, MEDIA_PERMISSION = 42;
    private boolean trusted(Uri uri) {
        Uri origin = Uri.parse(BuildConfig.VIQ_URL);
        return uri != null && "https".equals(uri.getScheme()) && origin.getHost().equals(uri.getHost())
            && effectivePort(origin) == effectivePort(uri) && uri.getUserInfo() == null;
    }
    private int effectivePort(Uri uri) { return uri.getPort() == -1 ? 443 : uri.getPort(); }

    @Override public void onCreate(Bundle state) {
        super.onCreate(state);
        LinearLayout layout = new LinearLayout(this); layout.setOrientation(LinearLayout.VERTICAL);
        ProgressBar progress = new ProgressBar(this, null, android.R.attr.progressBarStyleHorizontal);
        layout.addView(progress, new LinearLayout.LayoutParams(-1, 5));
        web = new WebView(this); layout.addView(web, new LinearLayout.LayoutParams(-1, 0, 1)); setContentView(layout);
        // Keep the app below system bars, including Android 15 edge-to-edge enforcement.
        layout.setOnApplyWindowInsetsListener((v, insets) -> {
            v.setPadding(insets.getSystemWindowInsetLeft(), insets.getSystemWindowInsetTop(), insets.getSystemWindowInsetRight(), insets.getSystemWindowInsetBottom());
            return insets;
        });
        WebSettings settings = web.getSettings();
        settings.setJavaScriptEnabled(true); settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false); settings.setAllowContentAccess(true);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setMediaPlaybackRequiresUserGesture(false); settings.setSafeBrowsingEnabled(true);
        CookieManager.getInstance().setAcceptCookie(true);
        CookieManager.getInstance().setAcceptThirdPartyCookies(web, false);
        WebView.setWebContentsDebuggingEnabled(BuildConfig.DEBUG);
        web.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri uri=request.getUrl();
                if (trusted(uri)) return false;
                if ("https".equals(uri.getScheme())) {
                    try { startActivity(new Intent(Intent.ACTION_VIEW, uri)); }
                    catch (Exception e) { message("লিংক খোলার ব্রাউজার পাওয়া যায়নি।"); }
                }
                return true;
            }
            @Override public void onReceivedError(WebView view, WebResourceRequest request, WebResourceError error) {
                if(request.isForMainFrame()) new AlertDialog.Builder(MainActivity.this).setTitle("VIQ সংযোগ")
                    .setMessage("ইন্টারনেট ও সার্ভার লিংক যাচাই করুন। ফ্রি সার্ভার চালু হতে সময় লাগতে পারে।")
                    .setPositiveButton("আবার চেষ্টা", (d,w)->web.loadUrl(BuildConfig.VIQ_URL)).setNegativeButton("বন্ধ",null).show();
            }
        });
        web.setWebChromeClient(new WebChromeClient() {
            @Override public void onProgressChanged(WebView view,int value) { progress.setProgress(value);progress.setVisibility(value==100?View.GONE:View.VISIBLE); }
            @Override public boolean onShowFileChooser(WebView view,ValueCallback<Uri[]> callback,FileChooserParams params) {
                if (!trusted(Uri.parse(view.getUrl()))) return false;
                if(fileCallback!=null)fileCallback.onReceiveValue(null);
                fileCallback=callback;
                Intent intent=new Intent(Intent.ACTION_OPEN_DOCUMENT);intent.addCategory(Intent.CATEGORY_OPENABLE);intent.setType("*/*");
                intent.putExtra(Intent.EXTRA_MIME_TYPES,new String[]{"image/png","image/jpeg","audio/*","video/mp4","video/webm"});
                try { startActivityForResult(intent,FILE_PICK); } catch(Exception e) {fileCallback.onReceiveValue(null);fileCallback=null;}
                return true;
            }
            @Override public void onPermissionRequest(PermissionRequest request) {
                if(!trusted(request.getOrigin()) || !trusted(Uri.parse(web.getUrl()))) {request.deny();return;}
                if(mediaRequest!=null){request.deny();return;}
                ArrayList<String> needed=new ArrayList<>();
                for(String resource:request.getResources()) {
                    if(resource.equals(PermissionRequest.RESOURCE_AUDIO_CAPTURE)) needed.add(Manifest.permission.RECORD_AUDIO);
                    else if(resource.equals(PermissionRequest.RESOURCE_VIDEO_CAPTURE)) needed.add(Manifest.permission.CAMERA);
                    else { request.deny();return; }
                }
                mediaRequest=request;
                new AlertDialog.Builder(MainActivity.this).setTitle("ক্যামেরা / মাইক্রোফোন চালু করবেন?")
                    .setMessage("শুধু আপনার শুরু করা ভয়েস রেকর্ড বা কল/লাইভে ব্যবহার হবে।")
                    .setPositiveButton("অনুমতি দিন",(d,w)->requestPermissions(needed.toArray(new String[0]),MEDIA_PERMISSION))
                    .setNegativeButton("না",(d,w)->denyMedia()).setOnCancelListener(d->denyMedia()).show();
            }
            @Override public void onPermissionRequestCanceled(PermissionRequest request) { if(mediaRequest==request)mediaRequest=null; }
        });
        web.setDownloadListener((url,agent,disposition,mime,length)->{
            Uri uri=Uri.parse(url);if(!trusted(uri))return;
            try {
                DownloadManager.Request req=new DownloadManager.Request(uri);
                String cookie=CookieManager.getInstance().getCookie(url);
                if(cookie!=null)req.addRequestHeader("Cookie",cookie);
                String name=URLUtil.guessFileName(url,disposition,mime);
                req.setTitle(name).setMimeType(mime).setNotificationVisibility(DownloadManager.Request.VISIBILITY_VISIBLE_NOTIFY_COMPLETED);
                req.setDestinationInExternalFilesDir(MainActivity.this,Environment.DIRECTORY_DOWNLOADS,name);
                ((DownloadManager)getSystemService(DOWNLOAD_SERVICE)).enqueue(req);message("ডাউনলোড শুরু হয়েছে।");
            } catch(Exception e) {message("ডাউনলোড করা যায়নি। ব্রাউজারে চেষ্টা করুন।");}
        });
        if(state!=null)web.restoreState(state);else web.loadUrl(BuildConfig.VIQ_URL);
    }
    private void message(String text){Toast.makeText(this,text,Toast.LENGTH_LONG).show();}
    private void denyMedia(){if(mediaRequest!=null){mediaRequest.deny();mediaRequest=null;}}
    @Override public void onRequestPermissionsResult(int code,String[] permissions,int[] results){
        super.onRequestPermissionsResult(code,permissions,results);
        if(code==MEDIA_PERMISSION&&mediaRequest!=null){
            boolean allowed=results.length>0;
            for(int result:results)if(result!=PackageManager.PERMISSION_GRANTED)allowed=false;
            if(allowed&&trusted(Uri.parse(web.getUrl())))mediaRequest.grant(mediaRequest.getResources());else mediaRequest.deny();
            mediaRequest=null;
        }
    }
    @Override protected void onActivityResult(int code,int result,Intent data){
        super.onActivityResult(code,result,data);
        if(code==FILE_PICK&&fileCallback!=null){fileCallback.onReceiveValue(WebChromeClient.FileChooserParams.parseResult(result,data));fileCallback=null;}
    }
    @Override public void onBackPressed(){if(web.canGoBack())web.goBack();else super.onBackPressed();}
    @Override protected void onSaveInstanceState(Bundle state){super.onSaveInstanceState(state);web.saveState(state);}
    @Override protected void onPause(){web.evaluateJavascript("window.dispatchEvent(new Event('pagehide'))",null);web.onPause();CookieManager.getInstance().flush();super.onPause();}
    @Override protected void onResume(){super.onResume();if(web!=null)web.onResume();}
    @Override protected void onDestroy(){denyMedia();if(fileCallback!=null)fileCallback.onReceiveValue(null);web.destroy();super.onDestroy();}
}
