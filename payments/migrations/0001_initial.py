# Generated by Django 5.1.7 on 2025-04-10 15:55

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("rides", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DriverEarning",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("commission", models.DecimalField(decimal_places=2, max_digits=10)),
                ("net_amount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("is_paid", models.BooleanField(default=False)),
                ("paid_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "driver",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="earnings",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "ride",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="driver_earnings",
                        to="rides.ride",
                    ),
                ),
            ],
            options={
                "verbose_name": "driver earning",
                "verbose_name_plural": "driver earnings",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="PaymentMethod",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "method_type",
                    models.CharField(
                        choices=[
                            ("mobile_money", "Mobile Money"),
                            ("cash", "Cash"),
                            ("card", "Card"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "provider",
                    models.CharField(
                        choices=[
                            ("mtn", "MTN Mobile Money"),
                            ("vodafone", "Vodafone Cash"),
                            ("airteltigo", "AirtelTigo Money"),
                            ("visa", "Visa"),
                            ("mastercard", "Mastercard"),
                        ],
                        max_length=20,
                    ),
                ),
                ("is_default", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "phone_number",
                    models.CharField(blank=True, max_length=15, null=True),
                ),
                (
                    "card_last_four",
                    models.CharField(blank=True, max_length=4, null=True),
                ),
                ("card_type", models.CharField(blank=True, max_length=20, null=True)),
                ("expiry_month", models.IntegerField(blank=True, null=True)),
                ("expiry_year", models.IntegerField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="payment_methods",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "payment method",
                "verbose_name_plural": "payment methods",
                "ordering": ["-is_default", "-created_at"],
            },
        ),
        migrations.CreateModel(
            name="Transaction",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("completed", "Completed"),
                            ("failed", "Failed"),
                            ("refunded", "Refunded"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("transaction_id", models.CharField(max_length=100, unique=True)),
                (
                    "provider_transaction_id",
                    models.CharField(blank=True, max_length=100, null=True),
                ),
                ("error_message", models.TextField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "payment_method",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="payments.paymentmethod",
                    ),
                ),
                (
                    "ride",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="transactions",
                        to="rides.ride",
                    ),
                ),
            ],
            options={
                "verbose_name": "transaction",
                "verbose_name_plural": "transactions",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="Wallet",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "balance",
                    models.DecimalField(decimal_places=2, default=0, max_digits=10),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="wallet",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "wallet",
                "verbose_name_plural": "wallets",
            },
        ),
        migrations.CreateModel(
            name="WalletTransaction",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "transaction_type",
                    models.CharField(
                        choices=[
                            ("deposit", "Deposit"),
                            ("withdrawal", "Withdrawal"),
                            ("ride_payment", "Ride Payment"),
                            ("refund", "Refund"),
                        ],
                        max_length=20,
                    ),
                ),
                ("amount", models.DecimalField(decimal_places=2, max_digits=10)),
                ("description", models.TextField()),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "ride",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="wallet_transactions",
                        to="rides.ride",
                    ),
                ),
                (
                    "wallet",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="transactions",
                        to="payments.wallet",
                    ),
                ),
            ],
            options={
                "verbose_name": "wallet transaction",
                "verbose_name_plural": "wallet transactions",
                "ordering": ["-created_at"],
            },
        ),
    ]
