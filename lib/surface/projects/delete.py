# Copyright 2015 Google Inc. All Rights Reserved.
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

"""Command to delete a project."""

from googlecloudsdk.api_lib.projects import util
from googlecloudsdk.api_lib.util import http_error_handler
from googlecloudsdk.calliope import base
from googlecloudsdk.command_lib.projects import flags
from googlecloudsdk.command_lib.projects import util as command_lib_util
from googlecloudsdk.core import log
from googlecloudsdk.core.console import console_io


@base.ReleaseTracks(base.ReleaseTrack.BETA, base.ReleaseTrack.GA)
class Delete(base.DeleteCommand):
  """Delete a project.

  Deletes the project with the given project ID.

  This command can fail for the following reasons:
  * The project specified does not exist.
  * The active account does not have Owner permissions for the given project.
  """

  detailed_help = {
      'EXAMPLES': """
          The following command deletes the project with the ID
          `example-foo-bar-1`:

            $ {command} example-foo-bar-1
      """,
  }

  def Collection(self):
    return command_lib_util.PROJECTS_COLLECTION

  def GetUriFunc(self):
    return command_lib_util.ProjectsUriFunc

  @staticmethod
  def Args(parser):
    flags.GetProjectFlag('delete').AddToParser(parser)

  # util.HandleKnownHttpErrors needs to be the first one to handle errors.
  # It needs to be placed after http_error_handler.HandleHttpErrors.
  @http_error_handler.HandleHttpErrors
  @util.HandleKnownHttpErrors
  def Run(self, args):
    projects = util.GetClient()
    messages = util.GetMessages()
    project_ref = command_lib_util.ParseProject(args.id)
    if not console_io.PromptContinue('Your project will be deleted.'):
      return None
    projects.projects.Delete(
        messages.CloudresourcemanagerProjectsDeleteRequest(
            projectId=project_ref.Name()))
    log.DeletedResource(project_ref)
    return util.DeletedResource(project_ref.Name())
