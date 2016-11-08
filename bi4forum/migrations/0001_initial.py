# -*- coding: utf-8 -*-
# Generated by Django 1.9.7 on 2016-11-08 00:14
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Category',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('precedence', models.IntegerField(default=0)),
            ],
            options={
                'verbose_name_plural': 'categories',
                'ordering': ['precedence'],
            },
        ),
        migrations.CreateModel(
            name='Post',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pub_date', models.DateTimeField(auto_now_add=True)),
                ('edit_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('full_text', models.TextField()),
                ('raw_text', models.TextField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SubForum',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('description', models.CharField(blank=True, default='', max_length=300, null=True)),
                ('precedence', models.IntegerField(default=0)),
                ('create_time', models.DateTimeField(auto_now_add=True)),
                ('category', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='forum.Category')),
            ],
            options={
                'ordering': ['category__precedence', 'precedence'],
            },
        ),
        migrations.CreateModel(
            name='Thread',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('pub_date', models.DateTimeField(auto_now_add=True)),
                ('edit_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('full_text', models.TextField()),
                ('raw_text', models.TextField()),
                ('thread_title', models.CharField(max_length=70, verbose_name='title')),
                ('is_attached', models.BooleanField(default=False)),
                ('post_add_date', models.DateTimeField(default=django.utils.timezone.now)),
                ('subforum', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='forum.SubForum')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
                ('users_disliked', models.ManyToManyField(related_name='threads_disliked', to=settings.AUTH_USER_MODEL)),
                ('users_liked', models.ManyToManyField(related_name='threads_liked', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-post_add_date', '-pub_date'],
            },
        ),
        migrations.CreateModel(
            name='UserProfile',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('signature', models.TextField(blank=True, default='', max_length=300, null=True)),
                ('avatar', models.ImageField(blank=True, max_length=200, null=True, upload_to='avatars')),
                ('new_email', models.EmailField(blank=True, default='', max_length=254, null=True)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='post',
            name='thread',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='forum.Thread'),
        ),
        migrations.AddField(
            model_name='post',
            name='user',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='post',
            name='users_disliked',
            field=models.ManyToManyField(related_name='posts_disliked', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AddField(
            model_name='post',
            name='users_liked',
            field=models.ManyToManyField(related_name='posts_liked', to=settings.AUTH_USER_MODEL),
        ),
    ]