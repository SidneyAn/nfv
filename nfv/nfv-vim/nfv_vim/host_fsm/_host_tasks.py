#
# Copyright (c) 2015-2016 Wind River Systems, Inc.
#
# SPDX-License-Identifier: Apache-2.0
#
import weakref

from nfv_common import debug
from nfv_common import state_machine

from nfv_vim.host_fsm._host_defs import HOST_EVENT
from nfv_vim.host_fsm._host_task_work import AuditHostServicesCompleteTaskWork
from nfv_vim.host_fsm._host_task_work import AuditHostServicesTaskWork
from nfv_vim.host_fsm._host_task_work import AuditInstancesTaskWork
from nfv_vim.host_fsm._host_task_work import CreateHostServicesTaskWork
from nfv_vim.host_fsm._host_task_work import DeleteHostServicesTaskWork
from nfv_vim.host_fsm._host_task_work import DisableHostServicesTaskWork
from nfv_vim.host_fsm._host_task_work import EnableHostServicesTaskWork
from nfv_vim.host_fsm._host_task_work import NotifyHostDisabledTaskWork
from nfv_vim.host_fsm._host_task_work import NotifyHostEnabledTaskWork
from nfv_vim.host_fsm._host_task_work import NotifyHostFailedTaskWork
from nfv_vim.host_fsm._host_task_work import NotifyHostServicesDeletedTaskWork
from nfv_vim.host_fsm._host_task_work import NotifyHostServicesDeleteFailedTaskWork
from nfv_vim.host_fsm._host_task_work import NotifyHostServicesDisabledTaskWork
from nfv_vim.host_fsm._host_task_work import NotifyHostServicesDisableFailedTaskWork
from nfv_vim.host_fsm._host_task_work import NotifyHostServicesEnabledTaskWork
from nfv_vim.host_fsm._host_task_work import NotifyInstancesHostDisabledTaskWork
from nfv_vim.host_fsm._host_task_work import NotifyInstancesHostDisablingTaskWork
from nfv_vim.host_fsm._host_task_work import QueryHypervisorTaskWork
from nfv_vim.host_fsm._host_task_work import WaitHostServicesCreatedTaskWork
from nfv_vim.host_fsm._host_task_work import WaitHostServicesDisabledTaskWork
from nfv_vim.host_fsm._host_task_work import WaitHostStabilizeTaskWork

DLOG = debug.debug_get_logger('nfv_vim.state_machine.host_task')


class AddHostTask(state_machine.StateTask):
    """
    Add Host Task
    """

    def __init__(self, host):
        from nfv_vim import objects

        self._host_reference = weakref.ref(host)
        task_work_list = list()
        if host.host_service_configured(objects.HOST_SERVICES.GUEST):
            task_work_list.append(CreateHostServicesTaskWork(
                self, host, objects.HOST_SERVICES.GUEST))
        super(AddHostTask, self).__init__(
            'add-host_%s' % host.name, task_work_list)

    @property
    def _host(self):
        """
        Returns the host
        """
        host = self._host_reference()
        return host

    def complete(self, result, reason):
        """
        Add Host Task Complete
        """
        if self.aborted():
            DLOG.debug("Task (%s) complete, but has been aborted." % self._name)
        else:
            DLOG.debug("Task (%s) complete." % self._name)

            event_data = dict()
            event_data['reason'] = reason

            if state_machine.STATE_TASK_RESULT.SUCCESS == result:
                self._host.fsm.handle_event(HOST_EVENT.TASK_COMPLETED, event_data)
            else:
                self._host.fsm.handle_event(HOST_EVENT.TASK_FAILED, event_data)


class DeleteHostTask(state_machine.StateTask):
    """
    Delete Host Task
    """

    def __init__(self, host):
        from nfv_vim import objects

        self._host_reference = weakref.ref(host)
        task_work_list = list()
        if host.host_service_configured(objects.HOST_SERVICES.COMPUTE):
            task_work_list.append(DeleteHostServicesTaskWork(
                self, host, objects.HOST_SERVICES.COMPUTE))
        if host.host_service_configured(objects.HOST_SERVICES.NETWORK):
            task_work_list.append(DeleteHostServicesTaskWork(
                self, host, objects.HOST_SERVICES.NETWORK))
        if host.host_service_configured(objects.HOST_SERVICES.GUEST):
            task_work_list.append(DeleteHostServicesTaskWork(
                self, host, objects.HOST_SERVICES.GUEST))
        if host.host_service_configured(objects.HOST_SERVICES.CONTAINER):
            task_work_list.append(DeleteHostServicesTaskWork(
                self, host, objects.HOST_SERVICES.CONTAINER))
        task_work_list.append(NotifyHostServicesDeletedTaskWork(
            self, host, force_pass=True))
        super(DeleteHostTask, self).__init__(
            'delete-host_%s' % host.name, task_work_list)

    @property
    def _host(self):
        """
        Returns the host
        """
        host = self._host_reference()
        return host

    def complete(self, result, reason):
        """
        Delete Host Task Complete
        """
        if self.aborted():
            DLOG.debug("Task (%s) complete, but has been aborted." % self._name)
        else:
            DLOG.debug("Task (%s) complete." % self._name)

            event_data = dict()
            event_data['reason'] = reason

            if state_machine.STATE_TASK_RESULT.SUCCESS == result:
                self._host.fsm.handle_event(HOST_EVENT.TASK_COMPLETED, event_data)
            else:
                self._host.fsm.handle_event(HOST_EVENT.TASK_FAILED, event_data)


class EnableHostTask(state_machine.StateTask):
    """
    Enable Host Task
    """

    def __init__(self, host):
        from nfv_vim import objects

        self._host_reference = weakref.ref(host)
        task_work_list = list()
        if host.host_service_configured(objects.HOST_SERVICES.CONTAINER):
            task_work_list.append(EnableHostServicesTaskWork(
                self, host, objects.HOST_SERVICES.CONTAINER))
        if host.host_service_configured(objects.HOST_SERVICES.COMPUTE):
            # We must wait for the compute service
            # to be created before enabling it.
            task_work_list.append(WaitHostServicesCreatedTaskWork(
                self, host, objects.HOST_SERVICES.COMPUTE))
            task_work_list.append(NotifyHostEnabledTaskWork(
                self, host, objects.HOST_SERVICES.COMPUTE))
            task_work_list.append(EnableHostServicesTaskWork(
                self, host, objects.HOST_SERVICES.COMPUTE))
        if host.host_service_configured(objects.HOST_SERVICES.NETWORK):
            # We must wait for the network service
            # to be created before enabling it.
            task_work_list.append(WaitHostServicesCreatedTaskWork(
                self, host, objects.HOST_SERVICES.NETWORK))
            task_work_list.append(EnableHostServicesTaskWork(
                self, host, objects.HOST_SERVICES.NETWORK))
        if host.host_service_configured(objects.HOST_SERVICES.GUEST):
            task_work_list.append(EnableHostServicesTaskWork(
                self, host, objects.HOST_SERVICES.GUEST))
        task_work_list.append(NotifyHostServicesEnabledTaskWork(
            self, host, force_pass=True))
        if host.host_service_configured(objects.HOST_SERVICES.COMPUTE):
            task_work_list.append(QueryHypervisorTaskWork(
                self, host, force_pass=True))
        super(EnableHostTask, self).__init__(
            'enable-host_%s' % host.name, task_work_list)

    @property
    def _host(self):
        """
        Returns the host
        """
        host = self._host_reference()
        return host

    def complete(self, result, reason):
        """
        Enable Host Task Complete
        """
        if self.aborted():
            DLOG.debug("Task (%s) complete, but has been aborted." % self._name)
        else:
            DLOG.debug("Task (%s) complete." % self._name)

            event_data = dict()
            event_data['reason'] = reason

            if state_machine.STATE_TASK_RESULT.SUCCESS == result:
                from nfv_vim import directors

                host_director = directors.get_host_director()
                host_director.host_enabled(self._host)

                self._host.fsm.handle_event(HOST_EVENT.TASK_COMPLETED, event_data)
            else:
                self._host.fsm.handle_event(HOST_EVENT.TASK_FAILED, event_data)


class DisableHostTask(state_machine.StateTask):
    """
    Disable Host Task
    """
    def __init__(self, host):
        from nfv_vim import objects

        self._host_reference = weakref.ref(host)

        if objects.HOST_PERSONALITY.WORKER in self._host.personality and \
                self._host.is_force_lock():
            # When a worker host is being disabled due to a force lock, we
            # want it to be rebooted. To do this we need to indicate that
            # the host services disable failed.
            notify_host_services_task = NotifyHostServicesDisableFailedTaskWork
        else:
            notify_host_services_task = NotifyHostServicesDisabledTaskWork

        task_work_list = list()
        if host.host_service_configured(objects.HOST_SERVICES.COMPUTE):
            task_work_list.append(DisableHostServicesTaskWork(
                self, host, objects.HOST_SERVICES.COMPUTE))
        if host.host_service_configured(objects.HOST_SERVICES.GUEST):
            task_work_list.append(DisableHostServicesTaskWork(
                self, host, objects.HOST_SERVICES.GUEST))
        if host.host_service_configured(objects.HOST_SERVICES.COMPUTE):
            task_work_list.append(QueryHypervisorTaskWork(
                self, host, force_pass=True))
        task_work_list.append(NotifyInstancesHostDisablingTaskWork(self, host))
        if host.host_service_configured(objects.HOST_SERVICES.COMPUTE):
            task_work_list.append(NotifyHostDisabledTaskWork(
                self, host, objects.HOST_SERVICES.COMPUTE))
        if host.host_service_configured(objects.HOST_SERVICES.NETWORK):
            task_work_list.append(NotifyHostDisabledTaskWork(
                self, host, objects.HOST_SERVICES.NETWORK))
        task_work_list.append(NotifyInstancesHostDisabledTaskWork(self, host))
        # Wait for latent post-live-migration cleanup
        if host.host_service_configured(objects.HOST_SERVICES.COMPUTE):
            task_work_list.append(WaitHostStabilizeTaskWork(
                self, host, timeout_in_secs=10))
        if host.host_service_configured(objects.HOST_SERVICES.CONTAINER):
            # Only disable the container services if the host is being locked
            # (or is already locked) and we are not running in a single
            # controller configuration. In a single controller configuration we
            # keep the container services running.
            if self._host.is_locking() or self._host.is_locked():
                from nfv_vim import directors
                sw_mgmt_director = directors.get_sw_mgmt_director()
                if not sw_mgmt_director.single_controller:
                    task_work_list.append(DisableHostServicesTaskWork(
                        self, host, objects.HOST_SERVICES.CONTAINER))
                    if not self._host.is_offline():
                        task_work_list.append(WaitHostServicesDisabledTaskWork(
                            self, host, objects.HOST_SERVICES.CONTAINER))
        task_work_list.append(notify_host_services_task(
            self, host, force_pass=True))
        if host.host_service_configured(objects.HOST_SERVICES.COMPUTE):
            task_work_list.append(QueryHypervisorTaskWork(
                self, host, force_pass=True))
        super(DisableHostTask, self).__init__(
            'disable-host_%s' % host.name, task_work_list)

    @property
    def _host(self):
        """
        Returns the host
        """
        host = self._host_reference()
        return host

    def complete(self, result, reason):
        """
        Disable Host Task Complete
        """
        if self.aborted():
            DLOG.debug("Task (%s) complete, but has been aborted." % self._name)
        else:
            from nfv_vim import directors

            host_director = directors.get_host_director()
            host_director.host_disabled(self._host)

            DLOG.debug("Task (%s) complete." % self._name)

            event_data = dict()
            event_data['reason'] = reason

            if state_machine.STATE_TASK_RESULT.SUCCESS == result:
                self._host.fsm.handle_event(HOST_EVENT.TASK_COMPLETED, event_data)
            else:
                self._host.fsm.handle_event(HOST_EVENT.TASK_FAILED, event_data)


class OfflineHostTask(state_machine.StateTask):
    """
    Offline Host Task
    """
    def __init__(self, host):
        from nfv_vim import objects

        self._host_reference = weakref.ref(host)

        task_work_list = list()
        if host.host_service_configured(objects.HOST_SERVICES.CONTAINER):
            # Only disable the container services if we are not running in a
            # single controller configuration. In a single controller
            # configuration we keep the container services running.
            from nfv_vim import directors
            sw_mgmt_director = directors.get_sw_mgmt_director()
            if not sw_mgmt_director.single_controller:
                task_work_list.append(DisableHostServicesTaskWork(
                    self, host, objects.HOST_SERVICES.CONTAINER))

        super(OfflineHostTask, self).__init__(
            'offline-host_%s' % host.name, task_work_list)

    @property
    def _host(self):
        """
        Returns the host
        """
        host = self._host_reference()
        return host

    def complete(self, result, reason):
        """
        Disable Host Task Complete
        """
        if self.aborted():
            DLOG.debug("Task (%s) complete, but has been aborted." % self._name)
        else:
            DLOG.debug("Task (%s) complete." % self._name)

            event_data = dict()
            event_data['reason'] = reason

            if state_machine.STATE_TASK_RESULT.SUCCESS == result:
                self._host.fsm.handle_event(HOST_EVENT.TASK_COMPLETED,
                                            event_data)
            else:
                self._host.fsm.handle_event(HOST_EVENT.TASK_FAILED, event_data)


class FailHostTask(state_machine.StateTask):
    """
    Fail Host Task
    """
    def __init__(self, host):
        self._host_reference = weakref.ref(host)
        task_work_list = list()
        task_work_list.append(NotifyHostFailedTaskWork(self, host))
        super(FailHostTask, self).__init__(
            'fail-host_%s' % host.name, task_work_list)

    @property
    def _host(self):
        """
        Returns the host
        """
        host = self._host_reference()
        return host

    def complete(self, result, reason):
        """
        Fail Host Task Complete
        """
        if self.aborted():
            DLOG.debug("Task (%s) complete, but has been aborted." % self._name)
        else:
            DLOG.debug("Task (%s) complete." % self._name)

            event_data = dict()
            event_data['reason'] = reason

            if state_machine.STATE_TASK_RESULT.SUCCESS == result:
                self._host.fsm.handle_event(HOST_EVENT.TASK_COMPLETED, event_data)
            else:
                self._host.fsm.handle_event(HOST_EVENT.TASK_FAILED, event_data)


class NotifyDeleteFailedTask(state_machine.StateTask):
    """
    Notify Delete Failed Host Task
    """
    def __init__(self, host):
        self._host_reference = weakref.ref(host)
        task_work_list = list()
        task_work_list.append(NotifyHostServicesDeleteFailedTaskWork(
            self, host, force_pass=True))
        super(NotifyDeleteFailedTask, self).__init__(
            'notify-delete-failed-host_%s' % host.name, task_work_list)

    @property
    def _host(self):
        """
        Returns the host
        """
        host = self._host_reference()
        return host

    def complete(self, result, reason):
        """
        Delete Failed Host Task Complete
        """
        if self.aborted():
            DLOG.debug("Task (%s) complete, but has been aborted." % self._name)
        else:
            DLOG.debug("Task (%s) complete." % self._name)

            event_data = dict()
            event_data['reason'] = reason

            if state_machine.STATE_TASK_RESULT.SUCCESS == result:
                self._host.fsm.handle_event(HOST_EVENT.TASK_COMPLETED, event_data)
            else:
                self._host.fsm.handle_event(HOST_EVENT.TASK_FAILED, event_data)


class NotifyDisableFailedTask(state_machine.StateTask):
    """
    Notify Disable Failed Host Task
    """
    def __init__(self, host):
        self._host_reference = weakref.ref(host)
        task_work_list = list()
        task_work_list.append(NotifyHostServicesDisableFailedTaskWork(
            self, host, force_pass=True))
        super(NotifyDisableFailedTask, self).__init__(
            'notify-disable-failed-host_%s' % host.name, task_work_list)

    @property
    def _host(self):
        """
        Returns the host
        """
        host = self._host_reference()
        return host

    def complete(self, result, reason):
        """
        Disable Failed Host Task Complete
        """
        if self.aborted():
            DLOG.debug("Task (%s) complete, but has been aborted." % self._name)
        else:
            DLOG.debug("Task (%s) complete." % self._name)

            event_data = dict()
            event_data['reason'] = reason

            if state_machine.STATE_TASK_RESULT.SUCCESS == result:
                self._host.fsm.handle_event(HOST_EVENT.TASK_COMPLETED, event_data)
            else:
                self._host.fsm.handle_event(HOST_EVENT.TASK_FAILED, event_data)


class NotifyEnabledHostTask(state_machine.StateTask):
    """
    Notify Enabled Host Task
    """
    def __init__(self, host):
        self._host_reference = weakref.ref(host)
        task_work_list = list()
        task_work_list.append(NotifyHostServicesEnabledTaskWork(
            self, host, force_pass=True))
        super(NotifyEnabledHostTask, self).__init__(
            'notify-enabled-host_%s' % host.name, task_work_list)

    @property
    def _host(self):
        """
        Returns the host
        """
        host = self._host_reference()
        return host

    def complete(self, result, reason):
        """
        Notify Enabled Host Task Complete
        """
        if self.aborted():
            DLOG.debug("Task (%s) complete, but has been aborted." % self._name)
        else:
            DLOG.debug("Task (%s) complete." % self._name)

            event_data = dict()
            event_data['reason'] = reason

            if state_machine.STATE_TASK_RESULT.SUCCESS == result:
                self._host.fsm.handle_event(HOST_EVENT.TASK_COMPLETED, event_data)
            else:
                self._host.fsm.handle_event(HOST_EVENT.TASK_FAILED, event_data)


class NotifyDisabledHostTask(state_machine.StateTask):
    """
    Notify Disabled Host Task
    """
    def __init__(self, host):
        from nfv_vim import objects

        self._host_reference = weakref.ref(host)
        task_work_list = list()
        if host.host_service_configured(objects.HOST_SERVICES.CONTAINER):
            # Only disable the container services if the host is being locked
            # and we are not running in a single controller configuration. In
            # a single controller configuration we keep the container services
            # running.
            if self._host.is_locking():
                from nfv_vim import directors
                sw_mgmt_director = directors.get_sw_mgmt_director()
                if not sw_mgmt_director.single_controller:
                    task_work_list.append(DisableHostServicesTaskWork(
                        self, host, objects.HOST_SERVICES.CONTAINER))
        task_work_list.append(NotifyHostServicesDisabledTaskWork(
            self, host, force_pass=True))
        super(NotifyDisabledHostTask, self).__init__(
            'notify-disabled-host_%s' % host.name, task_work_list)

    @property
    def _host(self):
        """
        Returns the host
        """
        host = self._host_reference()
        return host

    def complete(self, result, reason):
        """
        Notify Disabled Host Task Complete
        """
        if self.aborted():
            DLOG.debug("Task (%s) complete, but has been aborted." % self._name)
        else:
            DLOG.debug("Task (%s) complete." % self._name)

            event_data = dict()
            event_data['reason'] = reason

            if state_machine.STATE_TASK_RESULT.SUCCESS == result:
                self._host.fsm.handle_event(HOST_EVENT.TASK_COMPLETED, event_data)
            else:
                self._host.fsm.handle_event(HOST_EVENT.TASK_FAILED, event_data)


class AuditEnabledHostTask(state_machine.StateTask):
    """
    Audit Enabled Host Task
    """

    def __init__(self, host):
        from nfv_vim import objects

        self._host_reference = weakref.ref(host)
        task_work_list = list()
        if host.host_service_configured(objects.HOST_SERVICES.COMPUTE):
            task_work_list.append(AuditHostServicesTaskWork(
                self, host, objects.HOST_SERVICES.COMPUTE, force_pass=True))
        if host.host_service_configured(objects.HOST_SERVICES.NETWORK):
            task_work_list.append(AuditHostServicesTaskWork(
                self, host, objects.HOST_SERVICES.NETWORK, force_pass=True))
        if host.host_service_configured(objects.HOST_SERVICES.GUEST):
            task_work_list.append(AuditHostServicesTaskWork(
                self, host, objects.HOST_SERVICES.GUEST, force_pass=True))
        task_work_list.append(AuditHostServicesCompleteTaskWork(
            self, host))
        super(AuditEnabledHostTask, self).__init__(
            'audit-enabled-host_%s' % host.name, task_work_list)

    @property
    def _host(self):
        """
        Returns the host
        """
        host = self._host_reference()
        return host

    def complete(self, result, reason):
        """
        Audit Enabled Host Task Complete
        """
        if self.aborted():
            DLOG.debug("Task (%s) complete, but has been aborted." % self._name)
        else:
            DLOG.verbose("Task (%s) complete." % self._name)

            event_data = dict()
            event_data['reason'] = reason

            if state_machine.STATE_TASK_RESULT.SUCCESS == result:
                self._host.fsm.handle_event(HOST_EVENT.TASK_COMPLETED, event_data)
            else:
                self._host.fsm.handle_event(HOST_EVENT.TASK_FAILED, event_data)


class AuditDisabledHostTask(state_machine.StateTask):
    """
    Audit Disabled Host Task
    """
    def __init__(self, host):
        self._host_reference = weakref.ref(host)
        task_work_list = list()
        task_work_list.append(AuditInstancesTaskWork(
            self, host, force_pass=True))
        super(AuditDisabledHostTask, self).__init__(
            'audit-disabled-host_%s' % host.name, task_work_list)

    @property
    def _host(self):
        """
        Returns the host
        """
        host = self._host_reference()
        return host

    def complete(self, result, reason):
        """
        Audit Disabled Host Task Complete
        """
        if self.aborted():
            DLOG.debug("Task (%s) complete, but has been aborted." % self._name)
        else:
            DLOG.debug("Task (%s) complete." % self._name)

            event_data = dict()
            event_data['reason'] = reason

            if state_machine.STATE_TASK_RESULT.SUCCESS == result:
                self._host.fsm.handle_event(HOST_EVENT.TASK_COMPLETED, event_data)
            else:
                self._host.fsm.handle_event(HOST_EVENT.TASK_FAILED, event_data)
