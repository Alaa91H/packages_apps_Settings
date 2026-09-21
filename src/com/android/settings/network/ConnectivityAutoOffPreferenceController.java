/*
 * SPDX-FileCopyrightText: 2026 Evolution X
 * SPDX-License-Identifier: Apache-2.0
 */

package com.android.settings.network;

import android.content.Context;
import android.content.pm.PackageManager;
import android.provider.Settings;

import androidx.preference.ListPreference;
import androidx.preference.Preference;
import androidx.preference.PreferenceScreen;

import com.android.settings.core.BasePreferenceController;

/**
 * Controls the automatic shutdown timeout for Wi-Fi and Bluetooth.
 *
 * <p>The timeout is stored in {@link Settings.Global} in milliseconds. A value of {@code 0}
 * means the radio should never be turned off automatically.</p>
 */
public class ConnectivityAutoOffPreferenceController extends BasePreferenceController
        implements Preference.OnPreferenceChangeListener {

    public static final String KEY_WIFI_AUTO_OFF_TIMEOUT = "wifi_auto_off_timeout";
    public static final String KEY_BLUETOOTH_AUTO_OFF_TIMEOUT = "bluetooth_auto_off_timeout";

    private static final long TIMEOUT_DISABLED = 0L;
    private static final long TIMEOUT_MIN = 15_000L;
    private static final long TIMEOUT_MAX = 8 * 60 * 60 * 1000L;

    private ListPreference mPreference;

    public ConnectivityAutoOffPreferenceController(Context context, String preferenceKey) {
        super(context, preferenceKey);
    }

    @Override
    public int getAvailabilityStatus() {
        final PackageManager packageManager = mContext.getPackageManager();
        if (KEY_WIFI_AUTO_OFF_TIMEOUT.equals(getPreferenceKey())) {
            return packageManager.hasSystemFeature(PackageManager.FEATURE_WIFI)
                    ? AVAILABLE : UNSUPPORTED_ON_DEVICE;
        }
        if (KEY_BLUETOOTH_AUTO_OFF_TIMEOUT.equals(getPreferenceKey())) {
            return packageManager.hasSystemFeature(PackageManager.FEATURE_BLUETOOTH)
                    ? AVAILABLE : UNSUPPORTED_ON_DEVICE;
        }
        return UNSUPPORTED_ON_DEVICE;
    }

    @Override
    public void displayPreference(PreferenceScreen screen) {
        super.displayPreference(screen);
        mPreference = screen.findPreference(getPreferenceKey());
        if (mPreference != null) {
            mPreference.setOnPreferenceChangeListener(this);
            updateState(mPreference);
        }
    }

    @Override
    public void updateState(Preference preference) {
        super.updateState(preference);
        if (!(preference instanceof ListPreference)) {
            return;
        }

        final ListPreference listPreference = (ListPreference) preference;
        final long timeout = Settings.Global.getLong(
                mContext.getContentResolver(), getPreferenceKey(), TIMEOUT_DISABLED);
        updateListPreference(listPreference, timeout);
    }

    @Override
    public boolean onPreferenceChange(Preference preference, Object newValue) {
        final long timeout;
        try {
            timeout = Long.parseLong(String.valueOf(newValue));
        } catch (NumberFormatException e) {
            return false;
        }

        if (timeout != TIMEOUT_DISABLED
                && (timeout < TIMEOUT_MIN || timeout > TIMEOUT_MAX)) {
            return false;
        }

        final boolean written = Settings.Global.putLong(
                mContext.getContentResolver(), getPreferenceKey(), timeout);
        if (written && preference instanceof ListPreference) {
            updateListPreference((ListPreference) preference, timeout);
        }
        return written;
    }

    private void updateListPreference(ListPreference preference, long timeout) {
        String value = String.valueOf(timeout);
        int index = preference.findIndexOfValue(value);

        if (index < 0) {
            value = String.valueOf(TIMEOUT_DISABLED);
            index = preference.findIndexOfValue(value);
        }

        preference.setValue(value);
        if (index >= 0) {
            preference.setSummary(preference.getEntries()[index]);
        }
    }
}
