/*
 * Copyright (C) 2018 The Android Open Source Project
 *
 * Licensed under the Apache License, Version 2.0 (the "License");
 * you may not use this file except in compliance with the License.
 * You may obtain a copy of the License at
 *
 *      http://www.apache.org/licenses/LICENSE-2.0
 *
 * Unless required by applicable law or agreed to in writing, software
 * distributed under the License is distributed on an "AS IS" BASIS,
 * WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
 * See the License for the specific language governing permissions and
 * limitations under the License.
 */

package com.android.settings.deviceinfo;

import android.content.Context;
import android.telephony.TelephonyManager;

import com.android.settings.core.BasePreferenceController;

/** Controls availability of the Radio Info entry on the device details page. */
public final class RadioInfoPreferenceController extends BasePreferenceController {

    private final TelephonyManager mTelephonyManager;

    public RadioInfoPreferenceController(Context context, String key) {
        super(context, key);
        mTelephonyManager = context.getSystemService(TelephonyManager.class);
    }

    @Override
    public int getAvailabilityStatus() {
        return mTelephonyManager != null && mTelephonyManager.isVoiceCapable()
                ? AVAILABLE
                : UNSUPPORTED_ON_DEVICE;
    }
}
