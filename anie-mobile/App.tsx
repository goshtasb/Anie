import React from 'react';
import { View, StyleSheet, StatusBar } from 'react-native';
import { ShareIntentProvider, useShareIntent } from 'expo-share-intent';
import { MainDashboard } from './src/screens/MainDashboard';
import { ShareModal } from './src/components/ShareModal';

function RootNavigator() {
  const { hasShareIntent, shareIntent, resetShareIntent } = useShareIntent();

  // Share Extension Entry Point (Context B)
  // User shared content from another app (Safari, Twitter, etc.)
  if (hasShareIntent && shareIntent) {
    const intentType = shareIntent.type || 'text';
    const intentValue = shareIntent.webUrl || shareIntent.text || '';

    if (intentValue) {
      return (
        <View style={styles.shareContainer}>
          <StatusBar barStyle="light-content" />
          <ShareModal
            intentType={intentType}
            intentValue={intentValue}
            onClose={resetShareIntent}
          />
        </View>
      );
    }
  }

  // Main App Entry Point (Context A)
  // User tapped app icon on Home Screen
  return <MainDashboard />;
}

export default function App() {
  return (
    <ShareIntentProvider>
      <RootNavigator />
    </ShareIntentProvider>
  );
}

const styles = StyleSheet.create({
  shareContainer: {
    flex: 1,
    backgroundColor: 'transparent',
  },
});
