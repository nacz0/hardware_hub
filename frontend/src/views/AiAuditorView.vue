<script setup lang="ts">
import { computed, ref } from 'vue';
import { runInventoryAudit, type AuditIssue, type AuditReport } from '../api';

type SeverityGroup = {
  label: string;
  severity: 'high' | 'medium' | 'low';
  issues: AuditIssue[];
};

const report = ref<AuditReport | null>(null);
const error = ref('');
const isLoading = ref(false);

const severityOrder: SeverityGroup[] = [
  { label: 'High severity', severity: 'high', issues: [] },
  { label: 'Medium severity', severity: 'medium', issues: [] },
  { label: 'Low severity', severity: 'low', issues: [] },
];

const groupedIssues = computed<SeverityGroup[]>(() => {
  const issues = report.value?.issues ?? [];

  return severityOrder.map((group) => ({
    ...group,
    issues: issues.filter((issue) => issue.severity.toLowerCase() === group.severity),
  }));
});

const otherIssues = computed(() => {
  const knownSeverities = new Set(severityOrder.map((group) => group.severity));
  return (report.value?.issues ?? []).filter(
    (issue) => !knownSeverities.has(issue.severity.toLowerCase() as SeverityGroup['severity']),
  );
});

const totalIssues = computed(() => report.value?.issues.length ?? 0);

async function runAudit() {
  error.value = '';
  isLoading.value = true;

  try {
    report.value = await runInventoryAudit();
  } catch (caught) {
    report.value = null;
    error.value = getFriendlyAuditError(caught);
  } finally {
    isLoading.value = false;
  }
}

function getFriendlyAuditError(caught: unknown): string {
  const detail = caught instanceof Error ? caught.message : '';

  if (detail.toLowerCase().includes('forbidden')) {
    return 'Only admins can run the inventory audit.';
  }

  if (detail.toLowerCase().includes('unauthorized')) {
    return 'Please sign in again before running the inventory audit.';
  }

  if (detail) {
    return `The audit could not be completed. ${detail}`;
  }

  return 'The audit could not be completed. Please try again.';
}
</script>

<template>
  <section class="view">
    <div class="view-header">
      <p class="eyebrow">Inspection</p>
      <h2>AI Auditor</h2>
      <p>Review hardware records for missing data, unusual changes, and policy drift.</p>
    </div>

    <div class="audit-actions">
      <button type="button" :disabled="isLoading" @click="runAudit">
        {{ isLoading ? 'Running audit...' : 'Run audit' }}
      </button>
      <span v-if="isLoading">Checking inventory records through the backend auditor.</span>
    </div>

    <p v-if="error" class="error-banner">{{ error }}</p>

    <div v-if="report" class="audit-results">
      <article class="audit-summary">
        <span class="label">Summary</span>
        <p>{{ report.summary }}</p>
        <strong>{{ totalIssues }} {{ totalIssues === 1 ? 'issue' : 'issues' }}</strong>
      </article>

      <p v-if="!totalIssues" class="empty-state">No audit issues were returned.</p>

      <section
        v-for="group in groupedIssues"
        v-show="group.issues.length"
        :key="group.severity"
        class="audit-severity-group"
        :class="`severity-${group.severity}`"
      >
        <div class="audit-group-header">
          <h3>{{ group.label }}</h3>
          <span>{{ group.issues.length }}</span>
        </div>

        <ul class="audit-issue-list">
          <li v-for="issue in group.issues" :key="`${issue.itemId}-${issue.title}`" class="audit-issue">
            <div>
              <strong>{{ issue.title }}</strong>
              <span>Item #{{ issue.itemId }}</span>
            </div>
            <p>{{ issue.description }}</p>
            <p><b>Suggested action:</b> {{ issue.suggestedAction }}</p>
          </li>
        </ul>
      </section>

      <section v-if="otherIssues.length" class="audit-severity-group">
        <div class="audit-group-header">
          <h3>Other issues</h3>
          <span>{{ otherIssues.length }}</span>
        </div>

        <ul class="audit-issue-list">
          <li v-for="issue in otherIssues" :key="`${issue.itemId}-${issue.title}`" class="audit-issue">
            <div>
              <strong>{{ issue.title }}</strong>
              <span>Item #{{ issue.itemId }} - {{ issue.severity }}</span>
            </div>
            <p>{{ issue.description }}</p>
            <p><b>Suggested action:</b> {{ issue.suggestedAction }}</p>
          </li>
        </ul>
      </section>
    </div>
  </section>
</template>
