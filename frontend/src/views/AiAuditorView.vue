<template>
  <section class="view">
    <div class="view-header">
      <p class="eyebrow">Inspection</p>
      <h2>AI Auditor</h2>
      <p>Review hardware records for missing data, unusual changes, and policy drift.</p>
    </div>

    <div class="audit-box">
      <label>
        Audit prompt
        <textarea rows="5" placeholder="Summarize device records that need attention."></textarea>
      </label>
      <button type="button">Run audit</button>
    </div>
  </section>
</template>
