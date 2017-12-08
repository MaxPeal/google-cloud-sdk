# Copyright 2016 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""service-management remove-quota-override command."""

from googlecloudsdk.api_lib.service_management import base_classes
from googlecloudsdk.api_lib.service_management import consumers_flags
from googlecloudsdk.api_lib.service_management import services_util
from googlecloudsdk.calliope import base
from googlecloudsdk.calliope import exceptions
from googlecloudsdk.core import log
from googlecloudsdk.third_party.apitools.base.py import exceptions as apitools_exceptions


class RemoveQuota(base.Command, base_classes.BaseServiceManagementCommand):
  """Removes a quota override setting for a service and a project."""

  @staticmethod
  def Args(parser):
    """Args is called by calliope to gather arguments for this command.

    Args:
      parser: An argparse parser that you can use to add arguments that go
          on the command line after this command. Positional arguments are
          allowed.
    """
    views = services_util.GetCallerViews()

    consumers_flags.CONSUMER_PROJECT_FLAG.AddToParser(parser)
    consumers_flags.SERVICE_FLAG.AddToParser(parser)

    override = parser.add_mutually_exclusive_group(required=True)
    override.add_argument(
        '--consumer',
        action='store_true',
        default=False,
        help='Remove a consumer quota override. Or use --producer')
    override.add_argument(
        '--producer',
        action='store_true',
        default=False,
        help='Remove a producer quota override. Or use --consumer')

    parser.add_argument(
        '--view',
        default='CONSUMER',
        type=lambda x: str(x).upper(),
        choices=sorted(views.keys()),
        help=('The consumer settings view to use. Choose from {0}').format(
            ', '.join(sorted(views.keys()))))

    # TODO(user): Improve the documentation of these flags with extended help
    parser.add_argument(
        'quota_limit_key',
        help='The quota limit key in this format GroupName/LimitName.')

  def Run(self, args):
    """Run 'service-management remove-quota-override'.

    Args:
      args: argparse.Namespace, The arguments that this command was invoked
          with.

    Returns:
      The response from the consumer settings API call.

    Raises:
      HttpException: An http error response was received while executing api
          request.
    """
    # Shorten the request names for better readability
    get_request = (self.services_messages
                   .ServicemanagementServicesProjectSettingsGetRequest)
    patch_request = (self.services_messages
                     .ServicemanagementServicesProjectSettingsPatchRequest)

    views = services_util.GetCallerViews()

    # TODO(user): change this to a conditional update once the service
    # supports it. Until then...
    #
    # 1. Get the current list of Quota settings

    request = get_request(
        serviceName=args.service,
        consumerProjectId=args.consumer_project,
        view=views.get(args.view),
    )

    try:
      response = self.services_client.services_projectSettings.Get(request)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(services_util.GetError(error))

    # 2. Add the new quota setting to the current list
    override_removed = False
    if args.consumer:
      overrides = self.services_messages.QuotaSettings.ConsumerOverridesValue()
      if response.quotaSettings and response.quotaSettings.consumerOverrides:
        overrides = response.quotaSettings.consumerOverrides

      # Filter out the override to be deleted, if it is currently set
      new_overrides = []
      for override in overrides.additionalProperties:
        if override.key != args.quota_limit_key:
          new_overrides.append(override)
        else:
          override_removed = True
      overrides.additionalProperties = new_overrides

      quota_settings = self.services_messages.QuotaSettings(
          consumerOverrides=overrides
      )
    elif args.producer:
      overrides = self.services_messages.QuotaSettings.ProducerOverridesValue()
      if response.quotaSettings and response.quotaSettings.producerOverrides:
        overrides = response.quotaSettings.producerOverrides

      # Filter out the override to be deleted, if it is currently set
      new_overrides = []
      for override in overrides.additionalProperties:
        if override.key != args.quota_limit_key:
          new_overrides.append(override)
        else:
          override_removed = True
      overrides.additionalProperties = new_overrides

      quota_settings = self.services_messages.QuotaSettings(
          producerOverrides=overrides
      )

    if not override_removed:
      log.warn('No quota override found for "{0}"'.format(args.quota_limit_key))
      return

    project_settings = self.services_messages.ProjectSettings(
        quotaSettings=quota_settings,
    )

    update_mask = 'quota_settings.%s_overrides' % (
        'consumer' if args.consumer else 'producer')

    request = patch_request(
        serviceName=args.service,
        consumerProjectId=args.consumer_project,
        projectSettings=project_settings,
        updateMask=update_mask)

    try:
      # TODO(user): Add support for Operation completion, and --async flag
      result = self.services_client.services_projectSettings.Patch(request)
    except apitools_exceptions.HttpError as error:
      raise exceptions.HttpException(services_util.GetError(error))

    return services_util.ProcessOperationResult(result)
