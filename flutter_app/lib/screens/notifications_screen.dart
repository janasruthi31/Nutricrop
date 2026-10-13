import 'package:flutter/material.dart';
import '../l10n/app_localizations.dart';
import '../services/api_client.dart';
import '../theme/app_theme.dart';
import '../widgets/common_widgets.dart';

class NotificationsScreen extends StatefulWidget {
  const NotificationsScreen({super.key});

  @override
  State<NotificationsScreen> createState() => _NotificationsScreenState();
}

class _NotificationsScreenState extends State<NotificationsScreen> {
  List<dynamic> _notifications = [];
  bool _isLoading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _isLoading = true);
    try {
      final list = await ApiClient.instance.getNotifications();
      setState(() {
        _notifications = list;
        _error = null;
      });
    } catch (e) {
      setState(() => _error = 'Could not load notifications.');
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final l10n = AppLocalizations.of(context);
    return Scaffold(
      appBar: AppBar(title: Text(l10n.text('notifications'))),
      body: SafeArea(
        child: _isLoading
            ? const LoadingView(message: 'Loading notifications...')
            : _error != null
                ? ErrorStateView(message: _error!, onRetry: _load)
                : _notifications.isEmpty
                    ? const EmptyStateView(
                        icon: Icons.notifications_none_rounded,
                        title: 'No Notifications Yet',
                        subtitle: 'Application events and weather updates will appear here.',
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.all(16.0),
                        itemCount: _notifications.length,
                        itemBuilder: (ctx, i) {
                          final n = _notifications[i];
                          final isRead = n['is_read'] == 1;
                          final date = (n['created_at']?.toString() ?? '').split('T').first;

                          return Card(
                            color: isRead ? Colors.white : AppTheme.lightGreen.withOpacity(0.4),
                            child: ListTile(
                              leading: CircleAvatar(
                                backgroundColor: isRead ? Colors.grey.shade200 : AppTheme.lightGreen,
                                child: Icon(
                                  Icons.notifications_rounded,
                                  color: isRead ? Colors.grey : AppTheme.primaryGreen,
                                ),
                              ),
                              title: Text(
                                n['title'] ?? 'Notification',
                                style: TextStyle(fontWeight: isRead ? FontWeight.normal : FontWeight.bold),
                              ),
                              subtitle: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const SizedBox(height: 3),
                                  Text(n['message'] ?? '', style: const TextStyle(fontSize: 13)),
                                  const SizedBox(height: 4),
                                  Text(date, style: const TextStyle(fontSize: 11, color: Colors.grey)),
                                ],
                              ),
                              onTap: () async {
                                if (!isRead && n['id'] != null) {
                                  await ApiClient.instance.markNotificationRead(n['id']);
                                  _load();
                                }
                              },
                            ),
                          );
                        },
                      ),
      ),
    );
  }
}
