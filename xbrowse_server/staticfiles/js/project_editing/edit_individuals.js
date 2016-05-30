
$(document).ready(function() {
    var individuals = new IndividualSet(INDIVIDUALS);

    var indivsView = new IndividualListTable({
        collection: individuals,
        project_id: PROJECT_ID,
    });

    $('#edit-indivs-container').html(indivsView.render().el);

    window.bank = {};
    bank.individuals = individuals;
    bank.indivsView = indivsView;

});
